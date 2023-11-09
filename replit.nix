{ pkgs }: 
{
  deps = [
    pkgs.python39Full
    pkgs.python39Packages.flask
    # Add any other dependencies here, for example:
    pkgs.python39Packages.sqlalchemy
    pkgs.python39Packages.gunicorn
    pkgs.python39Packages.pytz
  ];
}