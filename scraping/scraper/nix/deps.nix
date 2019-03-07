{ fetchurl, python3Packages }:

{

  pytesseract = with python3Packages; buildPythonPackage rec {
    pname = "pytesseract";
    version = "0.2.2";
    name = "${pname}-${version}";
    src = fetchurl {
      url = "mirror://pypi/p/${pname}/${name}.tar.gz";
      sha256 = "0fd5qpfpcwg7n3kcii52r155076zmxbk4yg9ffjqfi3z9xvhqfn7";
    };
    propagatedBuildInputs = [ pillow ];
  };

  user-agent = with python3Packages; buildPythonPackage rec {
    pname = "user_agent";
    version = "0.1.9";
    name = "${pname}-${version}";
    src = fetchurl {
      url = "mirror://pypi/u/${pname}/${name}.tar.gz";
      sha256 = "1mf0x7mkaxyvl8mmncsc0wikxi5cijxp877a2nazkydfqind86lg";
    };
    buildInputs = [ pytest ];
    propagatedBuildInputs = [ six ];
  };

}
