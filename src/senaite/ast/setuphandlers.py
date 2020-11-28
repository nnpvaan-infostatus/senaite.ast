# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.AST.
#
# SENAITE.AST is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2020 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api
from bika.lims.api import security
from plone.registry.interfaces import IRegistry
from Products.CMFCore.permissions import ModifyPortalContent
from senaite.ast import logger
from senaite.ast import messageFactory as _
from senaite.ast import PRODUCT_NAME
from senaite.ast import PROFILE_ID
from senaite.ast.config import AST_SERVICE_CATEGORY
from senaite.ast.config import AST_SERVICE_KEYWORD
from zope.component import getUtility

# Tuples of (folder_id, folder_name, type)
SETUP_FOLDERS = [
    ("astpanels", "AST Panels", "ASTPanelFolder"),
]


def setup_handler(context):
    """Generic setup handler
    """
    if context.readDataFile("{}.txt".format(PRODUCT_NAME)) is None:
        return

    logger.info("{} setup handler [BEGIN]".format(PRODUCT_NAME.upper()))
    portal = context.getSite()

    # Setup folders
    add_setup_folders(portal)

    # Configure visible navigation items
    setup_navigation_types(portal)

    # Setup AST required contents
    setup_ast_category(portal)
    setup_ast_service(portal)

    logger.info("{} setup handler [DONE]".format(PRODUCT_NAME.upper()))


def add_setup_folders(portal):
    """Adds the initial folders in setup
    """
    logger.info("Adding setup folders ...")

    setup = api.get_setup()
    pt = api.get_tool("portal_types")
    ti = pt.getTypeInfo(setup)

    # Disable content type filtering
    ti.filter_content_types = False

    for folder_id, folder_name, portal_type in SETUP_FOLDERS:
        if setup.get(folder_id) is None:
            logger.info("Adding folder: {}".format(folder_id))
            setup.invokeFactory(portal_type, folder_id, title=folder_name)

    # Enable content type filtering
    ti.filter_content_types = True

    logger.info("Adding setup folders [DONE]")


def setup_navigation_types(portal):
    """Add additional types for navigation
    """
    logger.info("Setup navigation types ...")
    registry = getUtility(IRegistry)
    key = "plone.displayed_types"
    display_types = registry.get(key, ())

    new_display_types = set(display_types)
    to_display = map(lambda f: f[2], SETUP_FOLDERS)
    new_display_types.update(to_display)
    registry[key] = tuple(new_display_types)
    logger.info("Setup navigation types [DONE]")


def setup_ast_category(portal):
    """Setup a service category the AST service will be assigned to
    """
    name = AST_SERVICE_CATEGORY
    logger.info("Setup category '{}' ...".format(name))
    folder = api.get_setup().bika_analysiscategories
    exists = filter(lambda c: api.get_title(c) == name, folder.objectValues())
    if exists:
        logger.info("Category '{}' exists already [SKIP]".format(name))
        return

    # Create the category
    api.create(folder, "AnalysisCategory", title=name)
    logger.info("Setup category '{}' [DONE]".format(name))


def setup_ast_service(portal):
    """Setup an AST analysis service that will be used as the template for the
    creation of AST analyses. This service is not editable (used internally) and
    its keyword is "__ast"
    """
    key = AST_SERVICE_KEYWORD
    logger.info("Setup template service '{}' ...".format(key))
    folder = api.get_setup().bika_analysisservices
    exists = filter(lambda s: s.getKeyword() == key, folder.objectValues())
    if exists:
        logger.info("Service '{}' exists already [SKIP]".format(key))
        return

    # Get the category
    cat_name = AST_SERVICE_CATEGORY
    categories = api.get_setup().bika_analysiscategories.objectValues()
    category = filter(lambda c: api.get_title(c) == cat_name, categories)
    category = category[0]

    # Create the service
    title = _("Antibiotic Sensitivity")
    service = api.create(folder, "AnalysisService", Category=category,
                         title=title, Keyword=key)
    service.setShortTitle("AST")
    service.setScientificName(True)
    service.setStringResult(True)
    service.setPointOfCapture("ast")
    service.reindexObject()

    # Do not allow the modification of this service
    roles = security.get_valid_roles_for(service)
    security.revoke_permission_for(service, ModifyPortalContent, roles)
    logger.info("Setup template service '{}' [DONE]".format(key))


def pre_install(portal_setup):
    """Runs before the first import step of the *default* profile
    This handler is registered as a *pre_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} pre-install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)  # noqa
    portal = context.getSite()  # noqa

    logger.info("{} pre-install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_install(portal_setup):
    """Runs after the last import step of the *default* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)  # noqa
    portal = context.getSite()  # noqa

    logger.info("{} install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_uninstall(portal_setup):
    """Runs after the last import step of the *uninstall* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} uninstall handler [BEGIN]".format(PRODUCT_NAME.upper()))

    # https://docs.plone.org/develop/addons/components/genericsetup.html#custom-installer-code-setuphandlers-py
    profile_id = "profile-{}:uninstall".format(PRODUCT_NAME)
    context = portal_setup._getImportContext(profile_id)  # noqa
    portal = context.getSite()  # noqa

    logger.info("{} uninstall handler [DONE]".format(PRODUCT_NAME.upper()))
