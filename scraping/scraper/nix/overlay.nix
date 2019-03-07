self: super: {
  python3 = super.python3.override {
    packageOverrides = self': super':
      let
        deps = self'.callPackage ./deps.nix {};
        scraper = self'.callPackage ./scraper.nix {};
      in {
        inherit (deps) pytesseract user-agent;
        inherit scraper;
      };
  };
  python3Packages = self.python3.pkgs;
}
