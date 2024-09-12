import toml

from api.src.models import Config, Language, Models


class AppConfig:

    @classmethod
    def get_config(cls) -> Config:
        toml_file = 'api/config.toml'
        try:
            with open(toml_file, 'r', encoding='utf-8') as toml_contents:
                toml_config = toml.load(toml_contents)
        except (FileNotFoundError, toml.TomlDecodeError) as e:
            raise RuntimeError('Invalid or Missing configuration file')

        # convert supported languages to list which Config expects
        toml_config['static_analyzer']['supported_languages'] = \
            toml_config['static_analyzer']['supported_languages'].split(',')

        config_obj = Config(**toml_config['static_analyzer'])

        config_obj.language = cls._parse_language(
            toml_config.get('language', {})
        )

        config_obj.evaluate = cls._parse_evaluate(
            toml_config.get('evaluate', {})
        )

        return config_obj

    @classmethod
    def _parse_evaluate(cls, evaluate_config: dict) -> dict:
        models = evaluate_config.get('models', '').split(',')
        models = [model.strip() for model in models]
        assert (set(models).issubset(
            set([model.value for model in Models])))
        evaluate_config['models'] = [
            Models._value2member_map_[model] for model in models
        ]
        return evaluate_config

    @classmethod
    def _parse_language(cls, language_config: dict) -> dict:
        # Ensure we only have config for supported languages
        assert (set(language_config.keys()).issubset(
            set([lang.value for lang in Language])))

        return language_config
