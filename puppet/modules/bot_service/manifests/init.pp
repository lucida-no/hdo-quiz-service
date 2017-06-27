class bot_service (
  String $domain,
  String $app_path = '/opt/hdo-bot-service',
  String $app_user = 'botapp',
  Hash $app_environment = {},
  String $python_path = "${app_path}/venv/bin/python3",
  String $pip_path = "${app_path}/venv/bin/pip",
  String $gunicorn_path = "${app_path}/venv/bin/gunicorn",
  String $yarn_path = '/usr/bin/yarn',
  String $botadmin_path = "${app_path}/botadmin/static/botadmin",
  String $botadmin_build_cmd = "${yarn_path} run build",
  Integer $gunicorn_port = 8000,
  Integer $gunicorn_num_workers = 2,
  String $gunicorn_wsgi = 'bot_service.wsgi',
  String $db_name = $name,
  String $db_user = $name,
  String $db_password = lookup('bot_service_db_password'),
) {
  # App environment
  $db_env = {'DATABASE_URL' => "postgresql://${db_user}:${db_password}@localhost:5432/${db_name}"}
  $_app_environment = merge($app_environment, lookup('bot_service_environment', {merge => 'hash'}), $db_env)


  # Packages
  include bot_service::packages

  # Lets Encrypt cert
  class {'bot_service::letsencrypt':
    account => 'nikolaik@gmail.com'
  }

  bot_service::letsencrypt::certificate { "${name}_certs":
    domains => [$domain]
  }

  # Nginx
  include nginx

  bot_service::nginx { $domain:
    ssl_cert => "${::bot_service::letsencrypt::certificate_path}/${domain}.crt",
    ssl_key  => "${::bot_service::letsencrypt::certificate_path}/${domain}.key"
  }

  user { $app_user:
    ensure     => present,
    home       => "/home/${app_user}",
    managehome => true
  }

  file { "/home/${app_user}":
    ensure  => directory,
    owner   => $app_user
  }

  file { $app_path:
    ensure  => directory,
    owner   => $app_user
  }

  # Clone app
  vcsrepo { $app_path:
    ensure   => latest,
    user     => $app_user,
    provider => git,
    source   => 'https://github.com/holderdeord/hdo-quiz-service.git',
    revision => 'workymcworkson',
    require  => File[$app_path]
  }

  # Python virtualenv and requirements
  $venv_cmd = '/usr/bin/env python3 -m venv venv'
  exec { $venv_cmd:
    creates => "${app_path}/bin/activate",
    cwd     => $app_path,
    user    => $app_user,
    require => Package[$bot_service::packages::packages]
  }

  exec { "${pip_path} install -U pip wheel":
    cwd     => $app_path,
    user    => $app_user,
    require => Exec[$venv_cmd]
  }

  $pip_install = "${pip_path} install -r requirements.txt"
  exec { $pip_install:
    cwd     => $app_path,
    user    => $app_user,
    require => Exec[$venv_cmd]
  }

  # Supervisor
  class { 'supervisord':
    package_provider => 'apt',
    install_init     => false,
    service_name     => 'supervisor',
    executable       => '/usr/bin/supervisord',
    executable_ctl   => '/usr/bin/supervisorctl',
    config_include   => '/etc/supervisor/conf.d',
    config_file      => '/etc/supervisor/supervisord.conf'
  }

  supervisord::program { $name:
    command             => "${gunicorn_path} --bind 127.0.0.1:${gunicorn_port} --workers ${gunicorn_num_workers} ${gunicorn_wsgi}",
    directory           => $app_path,
    user                => $app_user,
    autostart           => true,
    autorestart         => true,
    program_environment => $_app_environment
  }

  # Postgres
  class { 'postgresql::server':}

  postgresql::server::db { $db_name:
    user     => $db_user,
    password => postgresql_password($db_user, $db_password),
  }

  # Redis
  include redis

  # Enviroment hash to array (ninja style)
  $_sep = ';;;;;;;;;;;' # FIXME: tried \n but could not escape the escaping
  $_env_var_template = "<% @_app_environment.each do |key,value| -%><%= key %>=<%= value %>${_sep}<% end -%>"
  $_app_environment_array = split(inline_template($_env_var_template), $_sep)

  # App: Django database migrations
  exec { "${python_path} manage.py migrate --noinput":
    cwd         => $app_path,
    user        => $app_user,
    environment => $_app_environment_array,
    require     => Exec[$pip_install]
  }

  # App: yarn install
  exec { $yarn_path:
    cwd     => $botadmin_path,
    user    => $app_user,
    require => Package[$bot_service::packages::packages]
  }

  # App: Build botadmin
  exec { $botadmin_build_cmd:
    cwd         => $botadmin_path,
    user        => $app_user,
    environment => $_app_environment_array,
    require     => Exec[$yarn_path]
  }

  # App: Django collect static
  exec { "${python_path} manage.py collectstatic --noinput -i node_modules -i bower_components":
    cwd         => $app_path,
    user        => $app_user,
    environment => $_app_environment_array,
    require     => Exec[$botadmin_build_cmd]
  }


}