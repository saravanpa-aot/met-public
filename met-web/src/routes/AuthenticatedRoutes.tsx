import React from "react";
import { Route, Routes } from "react-router-dom";
import NotFound from "./NotFound";
import LandingPage from "./LandingPage/LandingPage";
import { ThemeProvider } from "@mui/system";
import { BaseTheme, PublicTheme } from "../styles/Theme";
import UserService from "../services/UserServices";
import View from "../components/Form/View";

const AuthenticatedRoutes = () => {
  const adminRole = UserService.hasAdminRole();

  return (
    <ThemeProvider theme={BaseTheme}>
      <Routes>
        <Route path="/" element={<LandingPage/>} />
        <Route path="/survey" element={<View />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ThemeProvider>
  );
};

export default AuthenticatedRoutes;
