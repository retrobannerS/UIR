# LaTeX проект отчета УИР

## О шаблоне

За основу шаблона взят [оригинальный thesis-template](https://gitlab.com/skibcsit/thesis-template/-/tree/006cebaab233165578fafead97208f6a685d22b1/). Из изменений:

- Актуализированы титульные листы на момент мая 2025 года.
- Изменена структура проекта. Папки и файлы переименованы и пронумерованы.
- Удалены лишние файлы.
- Добавлены условные операторы для поддержания конфиденциальности проекта в публичных репозиториях.
- Переработана вставка подписей с датой для управления смещением как изображения, так и даты.
- Решена проблема с нумерацией приложений и корректного отображения их в оглавлении.
- В выходном файле при компиляции [ПЗ](./3-pz.tex) теперь не отображается аннотация к разделам. При компиляции [РСПЗ](./2-rspz.tex) — отображается.
- Добавлена небольшая автоматизация: количество источников, количество приложений.

Есть возможность создавать титульные листы с помощью программ, работающих с файлами `.docx`, и вставлять их в проект на LaTeX в виде готовых PDF файлов. Шаблоны можно найти в [этом репозитории](https://gitlab.com/skibcsit/thesis-titles/-/tree/faecf1e6a00953e4a54473d2750327d617bfb2d1/) или на [сайте кафедры](https://kaf22.ru/uchebno-issledovatelskaya-rabota/). Для вставки готового PDF в виде титульного листа достаточно в документах [РСПЗ](./2-rspz.tex) или [ПЗ](./3-pz.tex) раскомментировать соответствующие строки, указать путь к PDF и закомментировать строки, верстающие титульники в LaTeX.

## О навигации внутри папки

1. В папке [1-preamble](./1-preamble/) размещена преамбула. В ней задаются импортируемые пакеты, определение основных функций и логики их работы.
2. В папке [2-title](./2-titles/) размещены `.tex` и `.pdf` файлы для титульных листов. Выше описан процесс вставки титульных листов из `.docx`. Если же сборка титульных листов происходит из `.tex` файлов этой папки, то это происходит автоматически путём вставления определений шаблона (об этом ниже).
3. В папке [3-content](./3-content/) находятся файлы с определениями глобальных переменных шаблона, а также содержательная часть работы. 
   1. В файле [00-project-members-public(local)](./3-content/00-project-members-public.tex) можно определить глобальные переменные шаблоны: имя автора и научного руководителя, вид работы (УИР/НИР/ВКР), тему работы. 
   2. В файле [01-task-data](./3-content/01-task-data.tex) можно самостоятельно сделать утверждённое задание, вставить подписи, а также проставить оценку руководителя. 
   3. В остальных файлах пишется содержательная часть работы
4. Папка [4-listings](./4-listings/) предназначена для хранения файлов с программной реализацией для простой вставки в документ.
5. Папка [5-bibliography](./5-bibliography/) предназначена для файлов с библиографией. Советую использовать `Zotero` для автоматического заполнения данных файлов.
6. [Assets](./assets/) нужна для вспомогательных и основных рисунков.

## О конфиденциальности

Изначально в шаблоне используются оригинальные имена и подписи автора и научного руководителя, однако в публичный репозиторий было решено не отправлять сканы подписей и оригинальные имена.

Разделен файл [project-members](./3-content/00-project-members-public.tex) на `public`(имена в виде "заглушек") и `local` (Ваше имя и имя Вашего научного руководителя). `./3-content/00-project-members-local.tex` нужно создать у себя на компьютере перед сборкой.

Разделена [папка с росписями](./assets/signatures/) на `public` (подписи в виде "заглушки") и `local` (подписи Вас и Вашего научного руководителя). `local` нужно создать у себя на компьютере перед сборкой.

Для сборке проекта с кастомными подписями и именами нужно:
1. Переименовать `./3-content/00-project-members-public.tex` в `./3-content/00-project-members-local.tex` и указать в нем свои данные.
2. Создать папку `./assets/signatures/local/` и вложить в нее отсканированные подписи. По умолчанию их названия должны быть `author.png` и `supervisor.png`.
3. Собрать проект в обычном режиме.

## Сборка проекта

Сборка файла `1-task.tex` на `MacOS` осуществляется с помощью команды в папке с LaTeX проектом (должны быть установлены соответствующие инструменты для выполнения команды):

```{bash}
latexmk --shell-escape -synctex=1 -interaction=nonstopmode -file-line-error -xelatex -outdir="./out/" -auxdir="./.latex_tmp_files/" ./1-task.tex
```

Скомпилированный PDF файл можно будет найти в папке `out/`.

При желании можно воспользоваться автоматическими инструментами компилирования LaTeX, например `VS Code + LaTeX Workshop extension`.