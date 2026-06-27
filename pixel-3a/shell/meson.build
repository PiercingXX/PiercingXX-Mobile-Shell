project(
  'piercing-shell',
  version: '0.1.0',
  meson_version: '>=0.60.0',
)

python = import('python').find_installation('python3')

shell_subdir = 'piercing-shell'
shell_datadir = join_paths(get_option('datadir'), shell_subdir)

python.install_sources(
  [
    'src/main.py',
    'src/window.py',
    'src/app_index.py',
    'src/config.py',
  ],
  subdir: shell_subdir,
)

install_data(
  'src/style.css',
  install_dir: shell_datadir,
)

launcher_conf = configuration_data()
launcher_conf.set('python', python.full_path())
launcher_conf.set('shell_dir', join_paths(get_option('prefix'), shell_datadir))

configure_file(
  input: 'data/piercing-shell.in',
  output: 'piercing-shell',
  configuration: launcher_conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

desktop_conf = configuration_data()
desktop_conf.set('bindir', get_option('bindir'))

configure_file(
  input: 'data/io.piercingxx.PiercingShell.desktop.in',
  output: 'io.piercingxx.PiercingShell.desktop',
  configuration: desktop_conf,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications'),
)