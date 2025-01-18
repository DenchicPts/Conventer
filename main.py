import os
import sys
import configparser
import winreg

class RegistryManager:
    def __init__(self, app_name):
        self.app_name = app_name

    def add_to_registry(self, menu_structure):
        """
        Добавляет записи в реестр.
        menu_structure: dict - Структура вида {
            "png": {"ffmpeg": ["jpg", "webp"]}
        }
        """
        try:
            for file_ext, tools in menu_structure.items():
                base_key_path = rf"Software\Classes\.{file_ext}\shell\{self.app_name}"
                self._delete_registry_key(base_key_path)

                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Convert File")

                for tool, formats in tools.items():
                    tool_key_path = rf"{base_key_path}\{tool}"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, tool_key_path) as tool_key:
                        winreg.SetValueEx(tool_key, "", 0, winreg.REG_SZ, tool.capitalize())

                    for output_format in formats:
                        format_key_path = rf"{tool_key_path}\{output_format}"
                        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, format_key_path) as format_key:
                            command = tools[tool][output_format]
                            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{format_key_path}\command") as command_key:
                                winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command)

            print(f"Контекстное меню для '{self.app_name}' успешно обновлено!")
        except Exception as e:
            print(f"Ошибка при добавлении в реестр: {e}")

    def remove_from_registry(self, formats):
        """
        Удаляет записи из реестра для указанных форматов.
        formats: список расширений файлов
        """
        try:
            for file_ext in formats:
                key_path = rf"Software\Classes\.{file_ext}\shell\{self.app_name}"
                self._delete_registry_key(key_path)
            print("Записи реестра успешно удалены.")
        except Exception as e:
            print(f"Ошибка при удалении из реестра: {e}")

    def _delete_registry_key(self, key_path):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                while True:
                    try:
                        subkey = winreg.EnumKey(key, 0)
                        self._delete_registry_key(rf"{key_path}\{subkey}")
                    except OSError:
                        break
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass


class App:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.app_name = self.config["General"]["app_name"]
        self.command_template = self.config["General"]["command_template"]

        self.tools = dict(self.config["Tools"])
        self.supported_formats = {
            input_format: output_formats.split(", ")
            for input_format, output_formats in self.config["Formats"].items()
        }

        self.tool_options = {
            key: value for key, value in self.config["ToolOptions"].items()
        }

        self.registry = RegistryManager(self.app_name)

    def setup_registry(self):
        format_associations = {}

        for input_format, output_formats in self.supported_formats.items():
            format_associations[input_format] = {}
            for tool, tool_path in self.tools.items():
                format_associations[input_format][tool] = {}
                for output_format in output_formats:
                    command = self.command_template.format(
                        app=sys.argv[0],
                        tool=tool_path,
                        input_file="%1",
                        output_format=output_format
                    )
                    format_associations[input_format][tool][output_format] = command

        self.registry.remove_from_registry(self.supported_formats.keys())
        self.registry.add_to_registry(format_associations)


if __name__ == "__main__":
    config_path = "config.txt"
    if not os.path.exists(config_path):
        print("Конфигурационный файл не найден.")
        sys.exit(1)

    app = App(config_path)
    app.setup_registry()
