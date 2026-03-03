{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.ffmpeg
    pkgs.git
    pkgs.pkg-config
    pkgs.nodejs_20
  ];
}
