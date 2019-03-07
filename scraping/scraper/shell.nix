with import ./nix;

stdenv.mkDerivation {
  name = "env";
  buildInputs = with python3Packages; [
    python
    requests
    stem
    beautifulsoup4
    numpy
    pillow
    datadog
    boto3
    user-agent
    pytesseract
  ] ++ [
    tesseract
  ];
  shellHook = "export PYTHONPATH=$PWD:$PYTHONPATH";
}
