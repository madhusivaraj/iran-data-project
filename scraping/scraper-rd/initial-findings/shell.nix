with import <nixpkgs> {};

let

  pytesseract = with python3Packages; buildPythonPackage rec {
    name = "pytesseract-0.2.2";
    src = fetchurl {
      url = "mirror://pypi/p/pytesseract/${name}.tar.gz";
      sha256 = "0fd5qpfpcwg7n3kcii52r155076zmxbk4yg9ffjqfi3z9xvhqfn7";
    };
    propagatedBuildInputs = [ pillow ];
  };

in stdenv.mkDerivation {
  name = "env";
  buildInputs = [
    python3
    python3Packages.requests
    python3Packages.beautifulsoup4
    python3Packages.numpy
    python3Packages.pillow
    tesseract
    pytesseract
  ];
  shellHook = "export PYTHONPATH=.:$PYTHONPATH";
}
