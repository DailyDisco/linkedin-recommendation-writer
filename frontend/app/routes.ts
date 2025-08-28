import type { RouteConfig } from "@react-router/dev/routes";

export default [
  {
    path: "/",
    file: "routes/_index.tsx",
  },
  {
    path: "/generate",
    file: "routes/generate.tsx",
  },
  {
    path: "/history",
    file: "routes/history.tsx",
  },
  {
    path: "/about",
    file: "routes/about.tsx",
  },
] satisfies RouteConfig;
