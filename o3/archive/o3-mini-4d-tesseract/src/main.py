"""
4D Tesseract Ball Animation
--------------------------
This module provides a visualization of a ball bouncing inside a 4D tesseract (hypercube),
projected into 2D space using pygame.

The visualization demonstrates:
1. Generation of a 4D tesseract's vertices and edges
2. Projection from 4D to 2D space through rotation and perspective
3. Physics simulation of a ball bouncing within the tesseract boundaries
4. Real-time animation and rendering using pygame

Required Python version: 3.12.1
Dependencies: pygame==2.5.2

Example usage:
    python main.py

Controls:
    - Close window to exit
    - Animation runs automatically
"""

import pygame
import math
import sys
from config import WIDTH, HEIGHT, COLORS, FPS
from tesseract.geometry import generate_tesseract_vertices, generate_tesseract_edges
from tesseract.projection import project_point
from tesseract.physics import update_ball_position

# Initialize Pygame and set up display
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Bouncing Inside a Tesseract")
clock = pygame.time.Clock()
FPS = 60

# Define colors for visualization
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

def generate_tesseract_vertices():
    """
    Generate the 16 vertices of a tesseract with coordinates ±1 in each dimension.
    
    Returns:
        list: List of 4D coordinates [x, y, z, w] for each vertex
    """
    vertices = []
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                for w in (-1, 1):
                    vertices.append([x, y, z, w])
    return vertices

def generate_tesseract_edges(vertices):
    """
    Generate edges between tesseract vertices that differ in exactly one coordinate.
    
    Args:
        vertices (list): List of vertex coordinates
        
    Returns:
        list: List of tuples containing vertex indices that form edges
    """
    edges = []
    n = len(vertices)
    for i in range(n):
        for j in range(i + 1, n):
            # Count differing coordinates
            diff = sum(1 for k in range(4) if vertices[i][k] != vertices[j][k])
            if diff == 1:
                edges.append((i, j))
    return edges

# Initialize tesseract geometry
tesseract_vertices = generate_tesseract_vertices()
tesseract_edges = generate_tesseract_edges(tesseract_vertices)

# Set up projection parameters
scale = 200          # Scaling factor for drawing
distance = 3         # Distance used for perspective projection (3D -> 2D)
screen_center = (WIDTH // 2, HEIGHT // 2)

def project_point(point, angle):
    """
    Project a 4D point to 2D screen coordinates through rotation and perspective projection.
    
    Args:
        point (list): 4D coordinates [x, y, z, w]
        angle (float): Rotation angle in radians
        
    Returns:
        tuple: 2D screen coordinates (x, y)
    """
    x, y, z, w = point

    # Rotate in the x-w plane
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x_rot = x * cos_a - w * sin_a
    w_rot = x * sin_a + w * cos_a  # Stored for potential future use

    # Apply perspective projection with z-offset to prevent division by zero
    z_offset = 2
    factor = distance / (distance + z + z_offset)
    proj_x = x_rot * factor * scale + screen_center[0]
    proj_y = y * factor * scale + screen_center[1]
    return (int(proj_x), int(proj_y))

# Initialize ball properties
ball_pos = [0.0, 0.0, 0.0, 0.0]  # Starting at center of tesseract
ball_vel = [0.5, 0.3, 0.4, 0.2]  # Initial velocity in units per second
ball_radius = 10  # Drawing radius in pixels

# Define tesseract boundaries
min_bound = -1
max_bound = 1

# Initialize rotation angle
angle = 0

# Main game loop
running = True
while running:
    # Calculate time delta for smooth animation
    dt = clock.tick(FPS) / 1000  # Convert to seconds

    # Handle window close event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update ball physics - position and boundary collisions
    for i in range(4):
        ball_pos[i] += ball_vel[i] * dt
        if ball_pos[i] > max_bound:
            ball_pos[i] = max_bound
            ball_vel[i] *= -1  # Reverse velocity on collision
        elif ball_pos[i] < min_bound:
            ball_pos[i] = min_bound
            ball_vel[i] *= -1

    # Update rotation for dynamic view
    angle += 0.5 * dt

    # Render frame
    screen.fill(BLACK)  # Clear screen

    # Draw tesseract edges
    for edge in tesseract_edges:
        start = tesseract_vertices[edge[0]]
        end = tesseract_vertices[edge[1]]
        start_proj = project_point(start, angle)
        end_proj = project_point(end, angle)
        pygame.draw.line(screen, GRAY, start_proj, end_proj, 1)

    # Draw ball
    ball_proj = project_point(ball_pos, angle)
    pygame.draw.circle(screen, RED, ball_proj, ball_radius)

    # Update display
    pygame.display.flip()

# Clean up
pygame.quit()
sys.exit()
