import React, { useMemo, useContext } from 'react';
import { MenuItem, Select } from '@mui/material';
import { User, USER_GROUP, USER_STATUS } from 'models/user';
import { Palette } from 'styles/Theme';
import { UserManagementContext } from './UserManagementContext';
import { useAppSelector } from 'hooks';
import { USER_ROLES } from 'services/userService/constants';

interface ActionDropDownItem {
    value: number;
    label: string;
    action?: () => void;
    condition?: boolean;
}
export const ActionsDropDown = ({ selectedUser }: { selectedUser: User }) => {
    const { setAddUserModalOpen, setassignRoleModalOpen, setUser, setReassignRoleModalOpen } =
        useContext(UserManagementContext);
    const { roles } = useAppSelector((state) => state.user);

    const hasNoRole = (): boolean => {
        if (selectedUser.main_group) {
            return false;
        }
        return true;
    };

    const isAdmin = (): boolean => {
        if (selectedUser?.main_group == USER_GROUP.ADMIN.label) {
            return true;
        }
        return false;
    };

    const isViewer = (): boolean => {
        if (selectedUser?.main_group == USER_GROUP.VIEWER.label) {
            return true;
        }
        return false;
    };

    const ITEMS: ActionDropDownItem[] = useMemo(
        () => [
            {
                value: 1,
                label: 'Assign Role',
                action: () => {
                    setUser(selectedUser);
                    setassignRoleModalOpen(true);
                },
                condition:
                    hasNoRole() &&
                    roles.includes(USER_ROLES.EDIT_MEMBERS) &&
                    selectedUser.status_id == USER_STATUS.ACTIVE.value,
            },
            {
                value: 2,
                label: 'Assign to an Engagement',
                action: () => {
                    setUser(selectedUser);
                    setAddUserModalOpen(true);
                },
                condition:
                    !hasNoRole() && !isAdmin() && !isViewer() && selectedUser.status_id == USER_STATUS.ACTIVE.value,
            },
            {
                value: 3,
                label: 'Reassign Role',
                action: () => {
                    setUser(selectedUser);
                    setReassignRoleModalOpen(true);
                },
                condition:
                    !hasNoRole() &&
                    roles.includes(USER_ROLES.UPDATE_USER_GROUP) &&
                    selectedUser.status_id == USER_STATUS.ACTIVE.value,
            },
        ],
        [selectedUser.id, selectedUser.main_group],
    );

    return (
        <Select
            id={`action-drop-down-${selectedUser.id}`}
            value={0}
            fullWidth
            size="small"
            sx={{ backgroundColor: 'white', color: Palette.info.main }}
        >
            <MenuItem value={0} sx={{ fontStyle: 'italic', height: '2em' }} color="info" disabled>
                {'(Select One)'}
            </MenuItem>
            {ITEMS.filter((item) => item.condition).map((item) => (
                <MenuItem key={item.value} value={item.value} onClick={item.action}>
                    {item.label}
                </MenuItem>
            ))}
        </Select>
    );
};
