#!/bin/bash
# Скрипт для локальной сборки Family Tree

set -e

echo "=== Сборка Family Tree ==="

# Создаём директорию для сборки
BUILD_DIR="build-installer"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Копируем исполняемые файлы
echo "Копируем исполняемые файлы..."
cp dist/family_tree.exe "$BUILD_DIR/" 2>/dev/null || echo "family_tree.exe не найден"
cp dist/family_tree_web.exe "$BUILD_DIR/" 2>/dev/null || echo "family_tree_web.exe не найден"

# Создаём Inno Setup скрипт
echo "Создаём Inno Setup скрипт..."
VERSION=$(git describe --tags --always 2>/dev/null || echo "0.1.0")
sed "s/{{VERSION}}/$VERSION/g" installer/setup.iss > "$BUILD_DIR/setup.iss"

# Запускаем Inno Setup (если установлен)
if command -v iscc &> /dev/null; then
    echo "Запускаем Inno Setup..."
    cd "$BUILD_DIR"
    iscc setup.iss
    cd ..
    echo "Установочник создан: $BUILD_DIR/installer-output/"
else
    echo "Inno Setup не найден. Установите Inno Setup для создания установочника."
    echo "Скрипт создан: $BUILD_DIR/setup.iss"
    echo "Запустите: iscc $BUILD_DIR/setup.iss"
fi

echo "=== Сборка завершена ==="
