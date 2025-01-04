import common.api.sessionManager
import common.storage.manager

async def start():
    await common.storage.manager.init_database()
    await common.api.sessionManager.init_sessions()


async def stop():
    await common.api.sessionManager.close()
    await common.storage.manager.close()
