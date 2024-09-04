import toml

from api.src.models import Config, Language


class AppConfig:

    @classmethod
    def get_config(cls) -> Config:
        toml_file = 'api/config.toml'
        try:
            with open(toml_file, 'r', encoding='utf-8') as toml_contents:
                toml_config = toml.load(toml_contents)
        except (FileNotFoundError, toml.TomlDecodeError) as e:
            raise RuntimeError('Invalid or Missing configuration file')

        config_obj = Config(**toml_config['static_analyzer'])
        config_obj.language = toml_config.get('language', {})
        config_obj.evaluate = toml_config.get('evaluate', {})

        # Ensure we only have config for supported languages
        assert (set(toml_config.get('language', {}).keys()).issubset(
            set([lang.value for lang in Language])))

        return config_obj
