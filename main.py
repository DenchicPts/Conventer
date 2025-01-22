import os
import sys
import subprocess
import configparser
import winreg

class Tool:
    """Класс для представления инструмента конвертации."""
    def __init__(self, name, path, options):
        self.name = name
        self.path = path
        self.options = options

    def get_command(self, input_file, output_file, specific_options=""):
        """Формирует команду для выполнения конвертации."""
        options = self.options.get(specific_options, "")
        return [self.path, "-i", input_file] + options.split() + [output_file]

class RegistryManager:
    def __init__(self, app_name):
        self.app_name = app_name

    def add_to_registry(self, categories, tools):
        """
        Добавляет команды в реестр с использованием SubCommands.
        """
        try:
            for category, formats in categories.items():
                # Путь к категории (например, image, audio, video)
                category_key_path = rf"SystemFileAssociations\\{category}\\shell\\{self.app_name}"

                # Удаляем старые записи
                self._delete_registry_key(category_key_path, winreg.HKEY_CLASSES_ROOT)

                # Создаем основной раздел для Denchic_Converter
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, category_key_path) as category_key:
                    winreg.SetValueEx(category_key, "MUIVerb", 0, winreg.REG_SZ, "Convert to")
                    winreg.SetValueEx(category_key, "SubCommands", 0, winreg.REG_SZ, "")

                # Создаем раздел shell внутри Denchic_Converter
                shell_key_path = rf"{category_key_path}\\shell"

                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, shell_key_path) as shell_key:
                    for tool_name, tool in tools.items():
                        tool_key_path = rf"{shell_key_path}\\{tool_name}"

                        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, tool_key_path) as tool_key:
                            winreg.SetValueEx(tool_key, "SubCommands", 0, winreg.REG_SZ, "")

                            # Добавляем форматы файлов
                            for fmt in formats:
                                format_key_path = rf"{tool_key_path}\\shell\\{fmt}"

                                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, format_key_path) as format_key:
                                    winreg.SetValueEx(format_key, "MUIVerb", 0, winreg.REG_SZ, f"Convert to {fmt.upper()}")

                                    # Добавляем команду для формата
                                    command_key_path = rf"{format_key_path}\\command"
                                    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_key_path) as command_key:
                                        command = rf'"{os.path.abspath(sys.argv[0])}" {tool_name} "%1" {fmt}'
                                        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command)

            print(f"Контекстное меню для '{self.app_name}' успешно обновлено!")
        except Exception as e:
            print(f"Ошибка при добавлении в реестр: {e}")

    def remove_from_registry(self, categories):
        """
        Удаляет записи реестра, связанные с приложением.
        """
        try:
            # Удаляем разделы для форматов
            for fmt in set(fmt for formats in categories.values() for fmt in formats):
                format_key_path = rf"SystemFileAssociations\\.{fmt}\\shell\\{self.app_name}"
                self._delete_registry_key(format_key_path, winreg.HKEY_CLASSES_ROOT)

            print("Записи реестра успешно удалены.")
        except Exception as e:
            print(f"Ошибка при удалении из реестра: {e}")

    def _delete_registry_key(self, key_path, hive=winreg.HKEY_CLASSES_ROOT):
        """
        Удаляет ключ и его подпапки.
        """
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                while True:
                    try:
                        subkey = winreg.EnumKey(key, 0)
                        self._delete_registry_key(rf"{key_path}\\{subkey}", hive)
                    except OSError:
                        break
            winreg.DeleteKey(hive, key_path)
        except FileNotFoundError:
            pass

class App:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.app_name = self.config["General"]["app_name"]

        # Инициализация инструментов
        self.tools = {
            name: Tool(
                name=name,
                path=path,
                options={
                    key: value for key, value in self.config["ToolOptions"].items() if key.startswith(name)
                },
            )
            for name, path in self.config["Tools"].items()
        }

        self.categories = {
            category: [fmt.strip() for fmt in formats.split(",")]
            for category, formats in self.config["Formats"].items()
        }

        self.registry = RegistryManager(self.app_name)

    def setup_registry(self):
        """
        Настраивает контекстное меню через реестр.
        """
        self.registry.remove_from_registry(self.categories)
        self.registry.add_to_registry(self.categories, self.tools)

    def convert_file(self, tool_name, input_file, output_format):
        """
        Выполняет конвертацию файла с использованием указанного инструмента и формата.
        """
        if tool_name not in self.tools:
            print(f"Инструмент '{tool_name}' не найден.")
            return

        tool = self.tools[tool_name]
        base_name, _ = os.path.splitext(input_file)
        output_file = f"{base_name}.{output_format}"

        options_key = f"{tool_name}_{output_format}"
        command = tool.get_command(input_file, output_file, options_key)

        print(f"Выполняется команда: {' '.join(command)}")

        try:
            subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"Файл успешно конвертирован в '{output_file}'.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка выполнения команды: {e}")

def main():
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(exe_dir, "config.txt")

    if not os.path.exists(config_path):
        print("Конфигурационный файл не найден.")
        sys.exit(1)

    app = App(config_path)

    # Разделение на режимы работы
    if len(sys.argv) == 1:
        app.setup_registry()
    elif len(sys.argv) == 4:
        _, tool_name, input_file, output_format = sys.argv
        app.convert_file(tool_name, input_file, output_format)
    else:
        print("Неверное количество аргументов.")
        print("Использование:")
        print("  python main.py                - для настройки реестра")
        print("  python main.py <tool> <input_file> <output_format> - для конвертации файла")

if __name__ == "__main__":
    main()
