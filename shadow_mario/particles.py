"""Particle effects system."""

import math
import random
from typing import List, Callable, Optional

import pygame


class Particle:
    """Single particle."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: tuple,
        size: float,
        lifetime: float,
        gravity: float = 0.0,
        drag: float = 0.98,
        shrink: bool = True,
        fade: bool = True,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.initial_size = size
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.drag = drag
        self.shrink = shrink
        self.fade = fade
        self.active = True

    def update(self, dt: float) -> None:
        if not self.active:
            return

        self.x += self.vx * dt * 60  # Based on 60fps
        self.y += self.vy * dt * 60
        self.vy += self.gravity * dt * 60
        self.vx *= self.drag
        self.vy *= self.drag

        self.lifetime -= dt

        if self.lifetime <= 0:
            self.active = False
            return

        life_ratio = self.lifetime / self.max_lifetime

        if self.shrink:
            self.size = self.initial_size * life_ratio

        if self.fade:
            self.alpha = int(255 * life_ratio)
        else:
            self.alpha = 255

    def draw(self, screen: pygame.Surface, camera_offset: tuple[float, float] = (0, 0)) -> None:
        if not self.active or self.size <= 0:
            return

        cx = int(self.x - camera_offset[0])
        cy = int(self.y - camera_offset[1])

        if self.size < 2:
            # Small particles use pixel points
            if 0 <= cx < screen.get_width() and 0 <= cy < screen.get_height():
                color_with_alpha = self.color + (self.alpha,) if len(self.color) == 3 else self.color
                screen.set_at((cx, cy), color_with_alpha[:3])
        else:
            # Large particles use circles
            size_int = max(1, int(self.size))
            if len(self.color) == 3:
                color = self.color + (self.alpha,)
            else:
                color = self.color

            surf = pygame.Surface((size_int * 2, size_int * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size_int, size_int), size_int)
            screen.blit(surf, (cx - size_int, cy - size_int))


class ParticleSystem:
    """Particle system manager."""

    MAX_PARTICLES = 500

    def __init__(self) -> None:
        self.particles: List[Particle] = []
        self._emitters: dict[str, Callable] = {
            "jump_dust": self._emit_jump_dust,
            "coin_sparkle": self._emit_coin_sparkle,
            "fireball_trail": self._emit_fireball_trail,
            "damage_hit": self._emit_damage_hit,
            "boss_death": self._emit_boss_death,
            "land_dust": self._emit_land_dust,
            "combo_burst": self._emit_combo_burst,
        }

    def emit(self, emitter_name: str, x: float, y: float, **kwargs) -> None:
        """Generate particles using the specified emitter."""
        if emitter_name in self._emitters:
            self._emitters[emitter_name](x, y, **kwargs)

    def add_particle(self, particle: Particle) -> None:
        """Add a single particle."""
        if len(self.particles) < self.MAX_PARTICLES:
            self.particles.append(particle)

    def update(self, dt: float) -> None:
        """Update all particles."""
        i = 0
        while i < len(self.particles):
            self.particles[i].update(dt)
            if not self.particles[i].active:
                self.particles.pop(i)
            else:
                i += 1

    def draw(self, screen: pygame.Surface, camera_offset: tuple[float, float] = (0, 0)) -> None:
        """Draw all particles."""
        for p in self.particles:
            p.draw(screen, camera_offset)

    def clear(self) -> None:
        """Clear all particles."""
        self.particles.clear()

    # ---- Emitter implementations ----

    def _emit_jump_dust(self, x: float, y: float, direction: int = 0, **_) -> None:
        """Dust effect when jumping."""
        for _ in range(5):
            angle = random.uniform(math.pi * 0.7, math.pi * 1.3)
            speed = random.uniform(1.0, 3.0)
            vx = math.cos(angle) * speed + direction * 2
            vy = math.sin(angle) * speed
            color = (200, 200, 180)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(2, 4),
                lifetime=random.uniform(0.3, 0.6),
                gravity=0.05,
                drag=0.95,
            ))

    def _emit_land_dust(self, x: float, y: float, **_) -> None:
        """Dust effect when landing."""
        for _ in range(8):
            angle = random.uniform(-math.pi * 0.3, math.pi * 0.3)
            speed = random.uniform(1.5, 4.0)
            vx = math.cos(angle) * speed
            vy = -abs(math.sin(angle) * speed) * 0.5
            color = (180, 170, 150)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(3, 6),
                lifetime=random.uniform(0.4, 0.8),
                gravity=0.02,
                drag=0.92,
            ))

    def _emit_coin_sparkle(self, x: float, y: float, **_) -> None:
        """Sparkle effect when collecting coins."""
        # Golden particle burst
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 6.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            # Gold/yellow variants
            gold_variants = [
                (255, 215, 0),
                (255, 223, 0),
                (255, 200, 50),
                (255, 255, 100),
            ]
            color = random.choice(gold_variants)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(2, 5),
                lifetime=random.uniform(0.4, 0.8),
                gravity=-0.1,
                drag=0.94,
            ))
        # Center flash
        self.add_particle(Particle(
            x, y, 0, -1, (255, 255, 255),
            size=15,
            lifetime=0.3,
            gravity=0,
            drag=0.9,
            shrink=True,
        ))

    def _emit_fireball_trail(self, x: float, y: float, direction: int = 1, **_) -> None:
        """Fireball trail effect."""
        for _ in range(2):
            vx = random.uniform(-1, 1) - direction * 2
            vy = random.uniform(-1, 1)
            colors = [
                (255, 100, 0),
                (255, 150, 0),
                (255, 200, 50),
            ]
            color = random.choice(colors)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(2, 4),
                lifetime=random.uniform(0.2, 0.4),
                gravity=-0.05,
                drag=0.9,
            ))

    def _emit_damage_hit(self, x: float, y: float, **_) -> None:
        """Red particle effect when taking damage."""
        for _ in range(6):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = (255, 0, 0) if random.random() > 0.5 else (255, 50, 50)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(2, 4),
                lifetime=random.uniform(0.3, 0.6),
                gravity=0.05,
                drag=0.93,
            ))

    def _emit_combo_burst(self, x: float, y: float, **_) -> None:
        """Burst effect when combo milestone is reached."""
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3.0, 8.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2
            colors = [
                (255, 215, 0),
                (255, 100, 100),
                (100, 255, 100),
                (100, 150, 255),
                (255, 255, 255),
            ]
            color = random.choice(colors)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(2, 5),
                lifetime=random.uniform(0.5, 1.0),
                gravity=0.03,
                drag=0.94,
            ))
        # Center flash
        self.add_particle(Particle(
            x, y, 0, -0.5, (255, 255, 200),
            size=20,
            lifetime=0.4,
            gravity=0,
            drag=0.9,
        ))

    def _emit_boss_death(self, x: float, y: float, **_) -> None:
        """Boss death explosion effect."""
        # Outer explosion
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3.0, 10.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            colors = [
                (255, 100, 0),
                (255, 50, 0),
                (200, 0, 0),
                (255, 200, 0),
            ]
            color = random.choice(colors)
            self.add_particle(Particle(
                x, y, vx, vy, color,
                size=random.uniform(4, 10),
                lifetime=random.uniform(0.8, 1.5),
                gravity=0.02,
                drag=0.96,
            ))
        # Smoke
        for _ in range(10):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.0, 3.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2
            self.add_particle(Particle(
                x, y, vx, vy, (80, 80, 80),
                size=random.uniform(6, 12),
                lifetime=random.uniform(1.0, 2.0),
                gravity=-0.05,
                drag=0.97,
            ))
