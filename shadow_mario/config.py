import os
import pygame


class GameConfig:
    """加载并管理游戏配置文件。"""

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        res_dir = os.path.join(base_dir, "res")

        self.game_props = self._read_properties(os.path.join(res_dir, "app.properties"))
        self.msg_props = self._read_properties(os.path.join(res_dir, "message_en.properties"))

        # 窗口
        self.window_width = self._int("windowWidth")
        self.window_height = self._int("windowHeight")
        self.title = self.msg_props.get("title", "SHADOW MARIO")

        # 字体与图片路径（properties 中路径已含 res/ 前缀，直接相对于项目根目录）
        self.font_path = os.path.join(base_dir, self.game_props.get("font", "res/FSO8BITR.TTF"))
        self.background_image = os.path.join(base_dir, self.game_props.get("backgroundImage", "res/background.png"))

        # 关卡文件
        self.level1_file = os.path.join(base_dir, self.game_props.get("level1File", "res/level1.csv"))
        self.level2_file = os.path.join(base_dir, self.game_props.get("level2File", "res/level2.csv"))
        self.level3_file = os.path.join(base_dir, self.game_props.get("level3File", "res/level3.csv"))

        # 标题位置
        self.title_font_size = self._int("title.fontSize")
        self.title_x = self._float("title.x")
        self.title_y = self._float("title.y")

        # 分数/状态显示位置
        self.score_font_size = self._int("score.fontSize")
        self.score_x = self._float("score.x")
        self.score_y = self._float("score.y")

        self.message_font_size = self._int("message.fontSize")
        self.message_y = self._float("message.y")

        self.player_health_x = self._float("playerHealth.x")
        self.player_health_y = self._float("playerHealth.y")

        self.enemy_boss_health_x = self._float("enemyBossHealth.x")
        self.enemy_boss_health_y = self._float("enemyBossHealth.y")

        # 玩家
        self.player_image_right = os.path.join(base_dir, self.game_props["gameObjects.player.imageRight"])
        self.player_image_left = os.path.join(base_dir, self.game_props["gameObjects.player.imageLeft"])
        self.player_radius = self._float("gameObjects.player.radius")
        self.player_health = self._float("gameObjects.player.health")

        # 敌人
        self.enemy_image = os.path.join(base_dir, self.game_props["gameObjects.enemy.image"])
        self.enemy_radius = self._float("gameObjects.enemy.radius")
        self.enemy_damage = self._float("gameObjects.enemy.damageSize")
        self.enemy_max_displacement = self._float("gameObjects.enemy.maxRandomDisplacementX")
        self.enemy_speed = self._float("gameObjects.enemy.speed")
        self.enemy_random_speed = self._float("gameObjects.enemy.randomSpeed")

        # Boss
        self.boss_image = os.path.join(base_dir, self.game_props["gameObjects.enemyBoss.image"])
        self.boss_health = self._float("gameObjects.enemyBoss.health")
        self.boss_radius = self._float("gameObjects.enemyBoss.radius")
        self.boss_activation_radius = self._float("gameObjects.enemyBoss.activationRadius")
        self.boss_speed = self._float("gameObjects.enemyBoss.speed")

        # 平台
        self.platform_image = os.path.join(base_dir, self.game_props["gameObjects.platform.image"])
        self.platform_speed = self._float("gameObjects.platform.speed")

        # 飞行平台
        self.flying_platform_image = os.path.join(base_dir, self.game_props["gameObjects.flyingPlatform.image"])
        self.flying_platform_max_displacement = self._float("gameObjects.flyingPlatform.maxRandomDisplacementX")
        self.flying_platform_half_length = self._float("gameObjects.flyingPlatform.halfLength")
        self.flying_platform_half_height = self._float("gameObjects.flyingPlatform.halfHeight")
        self.flying_platform_speed = self._float("gameObjects.flyingPlatform.speed")
        self.flying_platform_random_speed = self._float("gameObjects.flyingPlatform.randomSpeed")

        # 金币
        self.coin_image = os.path.join(base_dir, self.game_props["gameObjects.coin.image"])
        self.coin_radius = self._float("gameObjects.coin.radius")
        self.coin_value = self._int("gameObjects.coin.value")
        self.coin_speed = self._float("gameObjects.coin.speed")

        # 火球
        self.fireball_image = os.path.join(base_dir, self.game_props["gameObjects.fireball.image"])
        self.fireball_radius = self._float("gameObjects.fireball.radius")
        self.fireball_damage = self._float("gameObjects.fireball.damageSize")
        self.fireball_speed = self._float("gameObjects.fireball.speed")

        # 双倍分数道具
        self.double_score_image = os.path.join(base_dir, self.game_props["gameObjects.doubleScore.image"])
        self.double_score_radius = self._float("gameObjects.doubleScore.radius")
        self.double_score_max_frames = self._int("gameObjects.doubleScore.maxFrames")
        self.double_score_speed = self._float("gameObjects.doubleScore.speed")

        # 无敌道具
        self.invincible_image = os.path.join(base_dir, self.game_props["gameObjects.invinciblePower.image"])
        self.invincible_radius = self._float("gameObjects.invinciblePower.radius")
        self.invincible_max_frames = self._int("gameObjects.invinciblePower.maxFrames")
        self.invincible_speed = self._float("gameObjects.invinciblePower.speed")

        # 终点旗
        self.end_flag_image = os.path.join(base_dir, self.game_props["gameObjects.endFlag.image"])
        self.end_flag_radius = self._float("gameObjects.endFlag.radius")
        self.end_flag_speed = self._float("gameObjects.endFlag.speed")

        # 字体（需要在 pygame.init() 和 set_mode 之后才能创建）
        self.status_font = pygame.font.Font(self.font_path, self.score_font_size)
        self.title_font = pygame.font.Font(self.font_path, self.title_font_size)
        self.instruction_font = pygame.font.Font(self.font_path, self.message_font_size)

    def _read_properties(self, filepath):
        """读取 .properties 文件，返回字典。"""
        result = {}
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    result[key.strip()] = value.strip()
        return result

    def _int(self, key):
        return int(self.game_props.get(key, "0"))

    def _float(self, key):
        return float(self.game_props.get(key, "0.0"))
