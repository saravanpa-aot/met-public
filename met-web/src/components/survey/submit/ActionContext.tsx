import React, { createContext, useState, useEffect } from 'react';
import { createDefaultSurvey, Survey } from 'models/survey';
import { useAppDispatch, useAppSelector } from 'hooks';
import { useNavigate, useParams } from 'react-router-dom';
import { openNotification } from 'services/notificationService/notificationSlice';
import { SurveyParams } from '../types';
import { getEmailVerification } from 'services/emailVerificationService';
import { getEngagement } from 'services/engagementService';
import { getSurvey } from 'services/surveyService';
import { submitSurvey } from 'services/submissionService';
import { Engagement, createDefaultEngagement } from 'models/engagement';
import { getSlugByEngagementId } from 'services/engagementSlugService';

interface SubmitSurveyContext {
    savedSurvey: Survey;
    isSurveyLoading: boolean;
    token?: string;
    isTokenValid: boolean;
    handleSubmit: (submissionData: unknown) => void;
    isSubmitting: boolean;
    savedEngagement: Engagement | null;
    isEngagementLoading: boolean;
    loadEngagement: null | (() => void);
    slug: string;
}

export const ActionContext = createContext<SubmitSurveyContext>({
    savedSurvey: createDefaultSurvey(),
    isSurveyLoading: true,
    isTokenValid: true,
    handleSubmit: (_submissionData: unknown) => {
        return;
    },
    isSubmitting: false,
    savedEngagement: null,
    isEngagementLoading: true,
    loadEngagement: null,
    slug: '',
});

export const ActionProvider = ({ children }: { children: JSX.Element }) => {
    const navigate = useNavigate();
    const dispatch = useAppDispatch();
    const isLoggedIn = useAppSelector((state) => state.user.authentication.authenticated);
    const { surveyId, token } = useParams<SurveyParams>();
    const [savedSurvey, setSavedSurvey] = useState<Survey>(createDefaultSurvey());
    const [isSurveyLoading, setIsSurveyLoading] = useState(true);
    const [isTokenValid, setTokenValid] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [savedEngagement, setSavedEngagement] = useState<Engagement | null>(null);
    const [isEngagementLoading, setIsEngagementLoading] = useState(true);
    const [slug, setSlug] = useState<string>('');

    const verifyToken = async () => {
        if (isLoggedIn) {
            setIsSurveyLoading(false);
            return;
        }

        if (!token) {
            navigate(`/not-found`);
            return;
        }

        try {
            const verification = await getEmailVerification(token);
            if (!verification || verification.survey_id !== Number(surveyId)) {
                throw new Error('verification not found or does not match survey');
            }
        } catch (error) {
            dispatch(
                openNotification({
                    severity: 'error',
                    text: 'Verification token is invalid.',
                }),
            );
            setTokenValid(false);
        } finally {
            setIsSurveyLoading(false);
        }
    };

    useEffect(() => {
        loadSurvey();
    }, []);
    const loadSurvey = async () => {
        if (isNaN(Number(surveyId))) {
            navigate('/not-found');
            dispatch(
                openNotification({
                    severity: 'error',
                    text: 'The survey id passed was erroneous',
                }),
            );
            return;
        }
        try {
            const loadedSurvey = await getSurvey(Number(surveyId));
            setSavedSurvey(loadedSurvey);
            setIsSurveyLoading(false);
            verifyToken();
        } catch (error) {
            dispatch(
                openNotification({
                    severity: 'error',
                    text: 'Error occurred while loading saved survey',
                }),
            );
        }
    };

    useEffect(() => {
        if (savedSurvey?.id !== 0) {
            loadEngagement();
        }
    }, [savedSurvey]);
    const loadEngagement = async () => {
        if (isNaN(Number(savedSurvey.engagement_id)) || !savedSurvey.engagement_id) {
            setSavedEngagement({
                ...createDefaultEngagement(),
                name: savedSurvey.name,
            });
            setIsEngagementLoading(false);
            return;
        }

        setIsEngagementLoading(true);
        try {
            const loadedEngagement = await getEngagement(Number(savedSurvey.engagement_id));
            setSavedEngagement(loadedEngagement);
            setIsEngagementLoading(false);
        } catch (error) {
            dispatch(
                openNotification({
                    severity: 'error',
                    text: 'Error occurred while loading saved engagement data',
                }),
            );
            setIsEngagementLoading(false);
        }
    };

    const handleFetchSlug = async () => {
        if (!savedSurvey.engagement_id) {
            return;
        }
        try {
            const response = await getSlugByEngagementId(savedSurvey.engagement_id);
            setSlug(response.slug);
        } catch (error) {
            setSlug('');
        }
    };

    useEffect(() => {
        handleFetchSlug();
    }, [savedSurvey.engagement_id]);

    const handleSubmit = async (submissionData: unknown) => {
        try {
            setIsSubmitting(true);
            await submitSurvey({
                survey_id: savedSurvey.id,
                submission_json: submissionData,
                verification_token: token ? token : '',
            });

            window.snowplow('trackSelfDescribingEvent', {
                schema: 'iglu:ca.bc.gov.met/submit-survey/jsonschema/1-0-0',
                data: { survey_id: savedSurvey.id, engagement_id: savedSurvey.engagement_id },
            });
            dispatch(
                openNotification({
                    severity: 'success',
                    text: 'Survey was successfully submitted',
                }),
            );
            navigate(`/${slug}`, {
                state: {
                    open: true,
                },
            });
        } catch (error) {
            dispatch(
                openNotification({
                    severity: 'error',
                    text: 'Error occurred during survey submission',
                }),
            );
            setIsSubmitting(false);
            verifyToken();
        }
    };

    return (
        <ActionContext.Provider
            value={{
                savedSurvey,
                isSurveyLoading,
                token,
                isTokenValid,
                handleSubmit,
                isSubmitting,
                savedEngagement,
                isEngagementLoading,
                loadEngagement,
                slug,
            }}
        >
            {children}
        </ActionContext.Provider>
    );
};
