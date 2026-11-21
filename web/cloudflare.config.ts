import { defineConfig } from "cf/config";

export default defineConfig({
  worker: {
    name: "jingyan-kaoyan",
    compatibilityDate: "2026-11-12",
    domains: ["jingyan.h0mura.de5.net"],
    assets: {
      notFoundHandling: "single-page-application",
    },
  },
});
