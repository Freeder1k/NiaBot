import common.api.sessionManager
import common.commands.commandListener
import common.logging
import common.logging
import common.storage.manager
import common.storage.playtimeData
from common.storage import serverConfig


async def start():
    await serverConfig.load_server_configs()
    await common.storage.manager.init_database()
    await common.api.sessionManager.init_sessions()


async def stop():
    await common.api.sessionManager.close()
    await common.storage.manager.close()
