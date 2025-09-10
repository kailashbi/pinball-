import pygame
import math

# Screen settings
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
BLACK = (0,0,0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Pinball Game with Parabolic Wall")


class Game:
    def __init__(self):
        self.score = 0
        self.lives = 10
        self.initial_launch = True  # Track if ball has been launched
        self.ball = Ball(
            position=(SCREEN_WIDTH - 27, SCREEN_HEIGHT - 60 - 10),
            radius=10,
            velocity=(0, 0),
        )
        self.launcher = Launcher(self.ball)
        self.left_flipper = Flipper(pivot=(200, 610), length=80, angle_range=(-30, 30))
        self.right_flipper = Flipper(
            pivot=(400, 610), length=80, angle_range=(210, 150)
        )
        
        self.gate = DynamicGate(
            position=(SCREEN_WIDTH - 25, SCREEN_HEIGHT - 415),  # Center of the launcher opening
            width=5,
            height=45,
            angle=60  # 60 degrees for a /-shaped tilt
        )


        

        
        self.boundary = Boundary()
        self.bumpers = [
            Bumper(position=(200, 250), radius=20),
            Bumper(position=(300, 190), radius=20),
            Bumper(position=(400, 250), radius=20),
            TriangularBumper([(400, 570), (450, 450), (450, 550)]),
            TriangularBumper([(150, 550), (200, 570), (150, 450)]),
        ]

        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def update(self):
        # Activate and adjust the gate when the ball leaves the launcher
        if self.initial_launch:
            self.launcher.update()
            if self.ball.in_play:
                self.initial_launch = False  # Disable further launches
        
        if self.ball.position.x > 550 and self.ball.position.y < 275 :
            self.gate.activate()  # Activate the gate
            self.gate.angle = math.radians(45)  # Rotate the gate to 45°

        # Update ball
        self.ball.update(
            self.boundary, self.left_flipper, self.right_flipper, self.bumpers
        )

        # Check collision with the tilted gate
        self.gate.check_collision(self.ball)

        # Update flippers
        self.left_flipper.update(pygame.key.get_pressed(), pygame.K_LEFT)
        self.right_flipper.update(pygame.key.get_pressed(), pygame.K_RIGHT)

        # Reset the gate when the ball is out of bounds
        if self.ball.position.y > SCREEN_HEIGHT:
            self.lives -= 1
            self.ball.reset()
            self.gate.deactivate()  # Deactivate the gate
            self.gate.angle = math.radians(0)  # Reset rotation
            self.initial_launch = True
            if self.lives <= 0:
                print("Game Over!")
                pygame.quit()

    def draw(self):
        screen.fill((0, 0, 0))

        # Draw game elements
        self.boundary.draw()
        self.ball.draw()
        self.launcher.draw()
        self.left_flipper.draw()
        self.right_flipper.draw()
        self.gate.draw()  # Draw the gate
        for bumper in self.bumpers:
            bumper.draw()

        # Draw score and lives
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 50))

        pygame.display.flip()



class Boundary:
    
    def __init__(self):
        # Outer boundary definitions
        self.rects = [
            pygame.Rect(0, 0, SCREEN_WIDTH, 10),  # Top
            pygame.Rect(0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10),  # Bottom
            pygame.Rect(0, 0, 10, SCREEN_HEIGHT),  # Left
            pygame.Rect(SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT),  # Right
        ]

        # Parabolic inner upper boundary points
        self.parabola_points = [
            (x, int(10 + 0.003 * (x - SCREEN_WIDTH // 2) ** 2))
            for x in range(10, SCREEN_WIDTH - 5, 10)
        ]

        self.quadrilaterals = [
            [(115, 560), (200, 600), (200, 620), (105, 560)],  # Quadrilateral 1
            [
                (400, 600),
                (SCREEN_WIDTH - 115, 560),
                (SCREEN_WIDTH - 105, 560),
                (400, 620),
            ],
            [(45, 300), (65, 350), (65, 500), (45, 550)],
            [
                (SCREEN_WIDTH - 67, 350),
                (SCREEN_WIDTH - 47, 300),
                (SCREEN_WIDTH - 47, 550),
                (SCREEN_WIDTH - 67, 500),
            ],
        ]

        self.triangles = [
            [(45, 688), (45, 560), (220, 688)],  # Left corner triangle
            [
                (SCREEN_WIDTH - 45, 688),
                (SCREEN_WIDTH - 45, 560),
                (SCREEN_WIDTH - 220, 688)
            ] # Right corner triangle
        ]

    def check_collision(self, ball):
        # Outer boundary collisions
        if (
            ball.position.x - ball.radius < 10
            or ball.position.x + ball.radius > SCREEN_WIDTH - 5
        ):
            ball.velocity.x *= -0.3  # Reflect horizontally
        if ball.position.y - ball.radius < 10:
            ball.velocity.y *= -0.3  # Reflect vertically

        # Parabolic boundary collision
        for i in range(len(self.parabola_points) - 1):
            point1 = pygame.Vector2(self.parabola_points[i])
            point2 = pygame.Vector2(self.parabola_points[i + 1])
            if self._check_line_collision(ball, point1, point2):
                break

        # Quadrilateral edge collisions
        for quad in self.quadrilaterals:
            for i in range(len(quad)):
                start = pygame.Vector2(quad[i])
                end = pygame.Vector2(quad[(i + 1) % len(quad)])
                if self._check_line_collision(ball, start, end):
                    break

        # Triangle edge collisions
        for tri in self.triangles:
            for i in range(len(tri)):
                start = pygame.Vector2(tri[i])
                end = pygame.Vector2(tri[(i + 1) % len(tri)])
                if self._check_line_collision(ball, start, end):
                    break

    def _check_line_collision(self, ball, start, end):
        line_vector = end - start
        point_to_ball = ball.position - start
        projection_length = (
            point_to_ball.dot(line_vector) / line_vector.length_squared()
        )
        projection_point = start + projection_length * line_vector

        # Check if the projection is on the line segment and within collision range
        if 0 <= projection_length <= 1:
            distance_to_line = ball.position.distance_to(projection_point)
            if distance_to_line <= ball.radius:
                # Calculate the normal vector of the line at the point of collision
                normal_vector = pygame.Vector2(-line_vector.y, line_vector.x).normalize()
                
                # Reflect the ball's velocity around the normal vector
                ball.velocity = ball.velocity.reflect(normal_vector)
                return True
        return False

    def draw(self):
        # for rect in self.rects:
        #     pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.lines(screen, GRAY, False, self.parabola_points, 5)

        # New line just left of the spring launcher
        line_x = SCREEN_WIDTH - 42  # Horizontal position left of the spring
        pygame.draw.line(screen, WHITE, (line_x, SCREEN_HEIGHT - 10), (line_x, 300), 5)
        line_x = SCREEN_WIDTH - 13  # Horizontal position left of the spring
        pygame.draw.line(
            screen, WHITE, (line_x, SCREEN_HEIGHT - 10), (line_x, 260), 5
        )  # Line from bottom to 350 height
        line_x = 40  # Horizontal position left of the spring
        pygame.draw.line(screen, WHITE, (line_x, SCREEN_HEIGHT - 10), (line_x, 290), 5)
        line_x = 12  # Horizontal position left of the spring
        pygame.draw.line(screen, WHITE, (line_x, SCREEN_HEIGHT - 10), (line_x, 260), 5)

        line_x = SCREEN_WIDTH - 110  # Horizontal position left of the spring
        pygame.draw.line(screen, WHITE, (line_x, 560), (line_x, 450), 10)  # Line from
        line_x = 110  # Horizontal position left of the spring
        pygame.draw.line(screen, WHITE, (line_x, 560), (line_x, 450), 10)  # Line from
        for quadrilateral in self.quadrilaterals:
            pygame.draw.polygon(screen, RED, quadrilateral, 0)
            pygame.draw.polygon(screen, WHITE, quadrilateral, 2)  # Draw only the borders

        for triangle in self.triangles:
            pygame.draw.polygon(screen, RED, triangle, 0)  # Fill
            pygame.draw.polygon(screen, WHITE, triangle, 2)  # Draw borders

class DynamicGate:
    def __init__(self, position, width, height, angle):
        self.position = pygame.Vector2(position)  # Center position of the gate
        self.width = width
        self.height = height
        self.angle = math.radians(angle)  # Initial angle in radians
        self.active = False  # Initially inactive
        self.color = WHITE

    def activate(self):
        """Activate the gate."""
        self.active = True

    def deactivate(self):
        """Deactivate the gate."""
        self.active = False

    def rotate_point(self, point, center, angle):
        """Rotate a point around a center by a given angle."""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        # Translate point back to origin
        translated_x = point[0] - center[0]
        translated_y = point[1] - center[1]

        # Rotate point
        rotated_x = translated_x * cos_a - translated_y * sin_a
        rotated_y = translated_x * sin_a + translated_y * cos_a

        # Translate point back to its original location
        return rotated_x + center[0], rotated_y + center[1]

    def get_points(self):
        """Calculate the points for the rotated gate."""
        # Unrotated rectangle corners
        half_width = self.width / 2
        half_height = self.height / 2

        corners = [
            (self.position.x - half_width, self.position.y - half_height),  # Top-left
            (self.position.x + half_width, self.position.y - half_height),  # Top-right
            (self.position.x + half_width, self.position.y + half_height),  # Bottom-right
            (self.position.x - half_width, self.position.y + half_height),  # Bottom-left
        ]

        # Rotate all corners around the center
        rotated_corners = [
            self.rotate_point(corner, self.position, self.angle) for corner in corners
        ]

        return rotated_corners

    def check_collision(self, ball):
        """Block the ball when the gate is active."""
        if not self.active:
            return

        # Simplify to an axis-aligned bounding box for collision checking
        points = self.get_points()
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        # Check if ball overlaps with the gate bounding box
        ball_rect = pygame.Rect(
            ball.position.x - ball.radius,
            ball.position.y - ball.radius,
            ball.radius * 2,
            ball.radius * 2
        )
        gate_rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
        if gate_rect.colliderect(ball_rect):
            ball.velocity.y *= -1  # Reflect ball's velocity

    def draw(self):
        """Draw the tilted gate if active."""
        if self.active:
            points = self.get_points()
            pygame.draw.polygon(screen, self.color, points)

class Ball:
    def __init__(self, position, radius, velocity):
        self.position = pygame.Vector2(position)
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.gravity = pygame.Vector2(0, 0.3)  # Downward force
        self.in_play = False  # Track if the ball has entered play

    def update(self, boundary, left_flipper, right_flipper, bumpers):
        if self.in_play:
            self.velocity += self.gravity
            self.position += self.velocity

            # Check boundary collisions
            boundary.check_collision(self)

            # Check collisions with flippers
            left_flipper.check_collision(self)
            right_flipper.check_collision(self)

            # Check collisions with bumpers
            for bumper in bumpers:
                bumper.check_collision(self)

    def reset(self):
        self.position = pygame.Vector2(
            SCREEN_WIDTH - 27, SCREEN_HEIGHT - 60 - self.radius
        )
        self.velocity = pygame.Vector2(0, 0)
        self.in_play = False

    def draw(self):
        pygame.draw.circle(
            screen, RED, (int(self.position.x), int(self.position.y)), self.radius
        )


class Launcher:
    def __init__(self, ball):
        self.ball = ball
        self.charge = 0  # Power charged by holding space bar
        self.max_charge = 15  # Maximum charge limit
        self.charge_rate = 0.3  # How quickly the launcher charges
        self.launch_speed = -2  # Base launch speed multiplier
        self.spring_base_y = SCREEN_HEIGHT - 60  # Fixed position for the spring
        self.spring_width = 20  # Width of the spring display
        self.spring_height = 50  # Base height of the spring

    def update(self):
        keys = pygame.key.get_pressed()

        # Charging the launcher when the space bar is pressed
        if keys[pygame.K_SPACE] and not self.ball.in_play:
            # Increase charge gradually but cap at max_charge
            self.charge = min(self.charge + self.charge_rate, self.max_charge)

        # Launch the ball when the space bar is released
        elif self.charge > 0 and not keys[pygame.K_SPACE]:
            # Set the ball's vertical speed based on the accumulated charge
            self.ball.velocity.y = self.charge * self.launch_speed
            self.ball.in_play = True  # Ball is now in play
            self.charge = 0  # Reset the charge

    def draw(self):
        # Draw the spring at a fixed position below the ball
        spring_x = SCREEN_WIDTH - 37
        compressed_height = int(
            self.spring_height - self.charge * 2
        )  # Compress based on charge
        spring_top_y = self.spring_base_y + (self.spring_height - compressed_height)

        # Draw the spring as a compressed rectangle
        pygame.draw.rect(
            screen, BLUE, (spring_x, spring_top_y, self.spring_width, compressed_height)
        )

        # Optional: Draw a border around the spring for better visibility
        pygame.draw.rect(
            screen,
            WHITE,
            (spring_x, spring_top_y, self.spring_width, compressed_height),
            2,
        )


class Flipper:
    def __init__(self, pivot, length, angle_range):
        self.pivot = pygame.Vector2(pivot)
        self.length = length
        self.angle_range = angle_range
        self.angle = angle_range[0]
        self.active = False
        self.color = BLUE

    def update(self, keys, activation_key):
        self.active = keys[activation_key]
        self.angle = self.angle_range[0] if self.active else self.angle_range[1]

    def check_collision(self, ball):
        # Calculate the flipper's end point
        flipper_end = self.pivot + pygame.Vector2(
            math.cos(math.radians(self.angle)) * self.length,
            math.sin(math.radians(self.angle)) * self.length,
        )

        # Line segment (flipper): self.pivot -> flipper_end
        flipper_vector = flipper_end - self.pivot
        ball_vector = ball.position - self.pivot

        # Project ball position onto the flipper segment
        flipper_length = flipper_vector.length()
        projection = ball_vector.dot(flipper_vector) / flipper_length

        # Clamp the projection to the segment
        projection = max(0, min(flipper_length, projection))
        closest_point = self.pivot + flipper_vector.normalize() * projection

        # Check distance from the ball to the closest point on the segment
        distance_to_flipper = closest_point.distance_to(ball.position)

        # Collision check
        if distance_to_flipper < ball.radius:
            # Reflect the ball's velocity based on the flipper's normal
            normal = (ball.position - closest_point).normalize()
            ball.velocity = (
                ball.velocity.reflect(normal) * 1
            )  # Adding some energy on collision
 
    def draw(self):
        flipper_end = self.pivot + pygame.Vector2(
            math.cos(math.radians(self.angle)) * self.length,
            math.sin(math.radians(self.angle)) * self.length,
        )
        pygame.draw.line(screen, self.color, self.pivot, flipper_end, 8)


class Bumper:
    def __init__(self, position, radius):
        self.position = pygame.Vector2(position)
        self.radius = radius
        self.color = YELLOW

    def check_collision(self, ball):
        if pygame.Vector2.distance_to(ball.position, self.position) < self.radius + ball.radius:
            ball.velocity *= -1

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.radius)


class TriangularBumper:
    def __init__(self, vertices):
        self.vertices = [pygame.Vector2(v) for v in vertices]
        self.color = RED

    def check_collision(self, ball):
        # Check if the ball collides with the triangle's edges
        for i in range(len(self.vertices)):
            start = self.vertices[i]
            end = self.vertices[(i + 1) % len(self.vertices)]
            if self._distance_to_edge(ball.position, start, end) < ball.radius:
                ball.velocity *= -1 

    def _distance_to_edge(self, point, start, end):
        # Calculate the perpendicular distance from a point to a line segment
        line = end - start
        length_squared = line.length_squared()
        if length_squared == 0:
            return point.distance_to(start)
        t = max(0, min(1, (point - start).dot(line) / length_squared))
        projection = start + t * line
        return point.distance_to(projection)

    def draw(self):
        # Draw the filled triangle
        pygame.draw.polygon(screen, self.color, [(int(v.x), int(v.y)) for v in self.vertices])
        
        # Draw the border
        pygame.draw.polygon(screen, BLACK, [(int(v.x), int(v.y)) for v in self.vertices], 2)


# Other classes: Ball, Launcher, Flipper, Bumper, TriangularBumper
# These remain similar but refined. Let me know if you'd like me to include them again!

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()