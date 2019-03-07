with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "env";
  buildInputs = [
    python3
    python3Packages.stem
    python3Packages.requests
  ] ++ lib.optional stdenv.isLinux tor;
}
