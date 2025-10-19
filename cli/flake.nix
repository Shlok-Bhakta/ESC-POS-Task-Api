{
  description = "Printer CLI - TUI for sending tasks to thermal printer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.default = pkgs.buildGoModule rec {
          pname = "printer-cli";
          version = "0.1.0";
          
          src = ./.;
          
          vendorHash = "sha256-JNUUCic7w+wIRc61DcMXNaOZJczNk+Is7A8on0jveSk=";
          
          subPackages = [ "." ];

          meta = with pkgs.lib; {
            description = "TUI for sending tasks to thermal printer";
            homepage = "https://github.com/Shlok-Bhakta/ESC-POS-Task-Api";
            license = licenses.mit;
            maintainers = [ ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            go
            gopls
            gotools
            go-tools
          ];
        };
      });
}
