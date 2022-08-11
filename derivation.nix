{ lib, python3, util-linux
, wrapGAppsHook, desktop-file-utils, hicolor-icon-theme }:

let
  python_deps = with python3.pkgs; [
    pygame
    pyyaml
  ];
in
python3.pkgs.buildPythonApplication rec {
  name = "ice-emblem";
  src = ./.;

  nativeBuildInputs = [
    wrapGAppsHook
    desktop-file-utils # needed for update-desktop-database
    hicolor-icon-theme # needed for postinstall script
  ];

  buildInputs = [];

  propagatedBuildInputs = python_deps;

  doCheck = true;
  checkInputs = buildInputs;

  meta = with lib; {
    description = "";
    homepage = "https://gitlab.com/Elinvention/ice-emblem";
    license = licenses.gpl3;
    platforms = platforms.linux;
  };
}
