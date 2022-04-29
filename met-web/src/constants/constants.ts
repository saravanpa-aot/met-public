const getFromEnv = (key: string, defaultValue: string = "") => {
  if (!key) return "";

  return process.env[key] || defaultValue;
};

//keycloak
export const Keycloak_Client = getFromEnv("REACT_APP_KEYCLOAK_CLIENT");

export const KEYCLOAK_URL = getFromEnv("REACT_APP_KEYCLOAK_URL");

export const KEYCLOAK_REALM = getFromEnv("REACT_APP_KEYCLOAK_REALM");

export const ADMIN_ROLE = "admin";

export const USER_RESOURCE_FORM_ID = getFromEnv(
  "REACT_APP_USER_RESOURCE_FORM_ID"
);

export const FORMIO_JWT_SECRET = getFromEnv("REACT_APP_FORMIO_JWT_SECRET");

export const KEYCLOAK_AUTH_URL = `${KEYCLOAK_URL}`;
