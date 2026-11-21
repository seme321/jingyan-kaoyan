import { bindings, defineConfig } from "cf/config";

export default defineConfig({
  worker: {
    name: "jingyan-kaoyan",
    compatibilityDate: "2026-11-21",
    entrypoint: "./worker/index.ts",
    domains: ["jingyan.h0mura.de5.net"],
    assets: {
      notFoundHandling: "single-page-application",
      runWorkerFirst: ["/api/*"],
    },
    observability: {
      enabled: true,
      traces: {
        enabled: true,
      },
    },
    env: {
      DB: bindings.d1({
        name: "jingyan-guestbook",
        id: "c0d0fa0a-1252-44d5-9afe-c8626231bb67",
      }),
      ADMIN_TOKEN: bindings.secret(),
    },
  },
});
