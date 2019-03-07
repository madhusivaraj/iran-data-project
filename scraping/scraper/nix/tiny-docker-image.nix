let
  
  pkgs = import <nixpkgs/pkgs/top-level> {
    localSystem.config = builtins.currentSystem;
    crossSystem.config = "x86_64-unknown-linux-musl";
    overlays = [
      (import ./overlay.nix)
    ];
  };

  py = pkgs.python3.withPackages (ps: with ps; [
    scraper
  ]);

in with pkgs; dockerTools.buildImage {
  name = "scraper-nix";

  runAsRoot = ''
    #!${stdenv.shell}
    ${dockerTools.shadowSetup}
    groupadd -r scraper
    useradd -r -g scraper -d /logs -M scraper
    mkdir /logs
    chown scraper:scraper /logs
  '';

  config = {
    Entrypoint = [
      "${su-exec}/bin/su-exec" "${busybox}/bin/sh" "-c"
      ''
        ${tor}/bin/tor &
        ${py}/bin/python ${../scripts/main.py} "$@"
      ''
    ];
    WorkingDir = "/logs";
    Volumes = {
      "/logs" = {};
    };
  };
}
