# -*- coding: utf-8 -*-

"""List and open JetBrains IDE projects.

Synopsis: <trigger> <filter>"""

import os
import re
from shutil import which
from xml.etree import ElementTree

from albertv0 import *

__iid__ = "PythonInterface/v0.3"
__prettyname__ = "Jetbrains IDE Projects"
__version__ = "1.2"
__trigger__ = "jb "
__author__ = "Markus Richter, Thomas Queste"
__dependencies__ = []

default_icon = os.path.dirname(__file__) + "/jetbrains.svg"
HOME_DIR = os.environ["HOME"]

paths = [  # <Name for config directory>, <possible names for the binary/icon>
    ["CLion", "clion", "jetbrains-clion"],
    ["DataGrip", "datagrip", "jetbrains-datagrip"],
    ["GoLand", "goland", "jetbrains-goland"],
    ["IntelliJIdea", "intellij-idea-ue-bundled-jre intellij-idea-ultimate-edition idea-ce-eap idea-ue-eap idea idea-ultimate", "jetbrains-idea"],
    ["PhpStorm", "phpstorm", "jetbrains-phpstorm"],
    ["PyCharm", "pycharm pycharm-eap charm", "jetbrains-pycharm"],
    ["WebStorm", "webstorm", "jetbrains-webstorm"],
    ["Rider", "rider", "jetbrains-rider"],
]


# find the executable path and icon of a program described by space-separated lists of possible binary-names
def find_exec(namestr: str):
    desktop_path = HOME_DIR + "/.local/share/applications/" + namestr + ".desktop";
    if not os.path.exists(desktop_path):
        return None
    with open(desktop_path, 'r') as file:
          desktop_file = file.read()
    icon_match = re.search("Icon=(.*)", desktop_file)
    exec_match = re.search("Exec=\"(.*)\"", desktop_file)
    return exec_match.group(1), icon_match.group(1)


# parse the xml at path, return all recent project paths and the time they were last open
def get_proj(path):
    r = ElementTree.parse(path).getroot()  # type:ElementTree.Element
    add_info = None
    items = dict()
    for o in r[0]:  # type:ElementTree.Element
        if o.attrib["name"] == 'recentPaths':
            for i in o[0]:
                items[i.attrib["value"]] = 0

        else:
            if o.attrib["name"] == 'additionalInfo':
                add_info = o[0]
    # add_info = <map></map>
    if len(items) == 0:
        return []

    if add_info is not None:
        for i in add_info:
            # i = <entry></entry>
            # i[0][0] = <RecentProjectMetaInfo></RecentProjectMetaInfo>
            for o in i[0][0]:
                # o = <option />
                if o.tag == "option" and o.attrib["name"] == 'projectOpenTimestamp':
                    items[i.attrib["key"]] = int(o.attrib["value"])
                    
    result = []
    for e in items:
        project_path = e.replace("$USER_HOME$", HOME_DIR)
        if project_path.endswith(".sln"):
            project_path_parts = project_path.split("/")
            del project_path_parts[-1]
            project_path = "/".join(project_path_parts)
        name_file_path = project_path + "/.idea/.name"
        if os.path.exists(name_file_path):
            with open(name_file_path, 'r') as name_file:
                project_name = name_file.read()
        else:
            project_name = project_path.split("/")[-1]
        result.append((items[e], e.replace("$USER_HOME$", HOME_DIR), project_name))
    return result


def handleQuery(query):
    if query.isTriggered:
        query.disableSort()

        binaries = {}
        projects = []

        for app in paths:
            config_path = "config/options/recentProjectDirectories.xml"
            if app[0] == "IntelliJIdea":
                config_path = "config/options/recentProjects.xml"
            if app[0] == "Rider":
                config_path = "config/options/recentSolutions.xml"

            # dirs contains possibly multiple directories for a program (eg. .GoLand2018.1 and .GoLand2017.3)
            dirs = [f for f in os.listdir(HOME_DIR) if
                    os.path.isdir(os.path.join(HOME_DIR, f)) and f.startswith("." + app[0])]
            # take the newest
            dirs.sort(reverse=True)
            if len(dirs) == 0:
                continue

            config_path = os.path.join(HOME_DIR, dirs[0], config_path)
            if not os.path.exists(config_path):
                continue

            # extract the binary name and icon
            binaries[app[0]] = find_exec(app[2])

            # add all recently opened projects
            projects.extend([[e[0], e[1], e[2], app[0]] for e in get_proj(config_path)])
        projects.sort(key=lambda s: s[0], reverse=True)

        # List all projects or the one corresponding to the query
        if query.string:
            projects = [p for p in projects if p[2].lower().find(query.string.lower()) != -1]

        items = []
        for p in projects:
            last_update = p[0]
            project_path = p[1]
            project_name = p[2]
            product_name = p[3]
            binary = binaries[product_name]
            if not binary:
                continue

            executable = binary[0]
            icon = binary[1]

            items.append(Item(
                id="-" + str(last_update),
                icon=icon,
                text=project_name,
                subtext=project_path,
                completion=__trigger__ + project_name,
                actions=[
                    ProcAction("Open in %s" % product_name, [executable, project_path])
                ]
            ))

        return items
