"""Генерация безопасного текстового описания PlantUML."""

import json


def to_plantuml(graph, max_depth):
    """Сформировать диаграмму; стрелка направлена к зависимости."""
    aliases = {node: f'n{index}' for index, node in enumerate(graph.nodes)}
    lines = ['@startuml', 'left to right direction',
             'title Alpine APK dependency graph', 'skinparam shadowing false']
    for node in graph.nodes:
        label = json.dumps(node, ensure_ascii=False)
        lines.append(f'component {label} as {aliases[node]}')
    for parent, children in graph.edges.items():
        for child in children:
            lines.append(f'{aliases[parent]} --> {aliases[child]}')
    lines.append(f'legend right\n  Root depth = 0; max depth = {max_depth}'
                 '\n  Arrow: package -> dependency\nendlegend')
    lines.append('@enduml')
    return '\n'.join(lines) + '\n'
