{ python3Packages, tesseract, pytesseract, user-agent }:

python3Packages.buildPythonPackage rec {
  name = "scraper";
  src = ../.;
  propagatedBuildInputs = with python3Packages; [
    python
    requests
    stem
    beautifulsoup4
    numpy
    pillow
    datadog
    boto3
  ] ++ [
    tesseract
    pytesseract
    user-agent
  ];
}
