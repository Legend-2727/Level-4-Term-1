#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// OpenGL / GLUT Headers
#ifdef __APPLE__
#include <GLUT/glut.h> // Use GLUT framework on macOS
#else
#include <GL/glut.h> // Use standard GLUT location on Linux/Windows
#endif

// Camera position
float cameraX = 40.0f;
float cameraY = 23.0f;
float cameraZ = 40.0f;

// Where the camera is looking
float lookX = 0.0f;
float lookY = -2.3f;
float lookZ = 0.0f;

// Up direction
float upX = 0.0f;
float upY = 1.0f;
float upZ = 0.0f;

// float ballY = -1.5f;         // Initial height (bottom plane level)
float ballY = -1.0f;         // Initial height (bottom plane level)
float ballX = 0.0f;         // Initial horizontal position
float ballZ = 0.0f;         // Initial depth position
float ballSpeed = 40.0f;     // Vertical speed
float gravity = -9.8f;     // Simulated gravity
float bounceFactor = 0.8f;   // How much speed is retained after bounce

bool isPaused = true; // Pause state

/* ---------- globals that describe floor ---------- */
const float floorSize   = 10.0f;   // = 3.0 in your drawCube()
const float floorHeight = -10.0f;         // height of the floor
const int   checkCount = 20;
const float tileSize   = (2 * floorSize) / checkCount;
const float ballR      = 0.8f;         // sphere radius

/* centres allowed between [-max, +max] */
// const float maxCentre  = floorSize - ballR;          // 3.0 – 0.15 = 2.85
// const int   firstTile  = static_cast<int>(( floorSize - maxCentre) / tileSize); // 0
// const int   lastTile   = checkCount - 1 - firstTile;    
const float floorMinSize = -5;
const float floorMaxSize = 20.0;                       // 19
float ballminC_XY = floorMinSize + ballR + 1;   //  -2.85
float ballmaxC_XY =  floorMaxSize - ballR;   //  +2.85
float ballminC_Y = -floorHeight + ballR ;   //  -2.85
float ballmaxC_Y =  floorHeight - ballR;   //  +2.85

float vx = 0.0f, vy = 0.0f, vz = 0.0f;
const float deltaTime = 0.006f; // Slow motion

bool initialized = false; // For random ball direction


inline float randf(float a, float b)
{
    return a + static_cast<float>(rand()) / RAND_MAX * (b - a);
}


struct Color
{
    float r, g, b;
};
// How much to move the camera each key press
const float moveSpeed = 0.5f;

void drawCube(float size = 1.0f)
{
    float topSize = size * 2.0f;
    float bottomSize = size * 2.0f;

    // ---- Top face ----
    glBegin(GL_QUADS);
    glColor3f(0.6f, 0.6f, 0.9f); // Top (Purple)
    glVertex3f(topSize, size, -topSize);
    glVertex3f(-topSize, size, -topSize);
    glVertex3f(-topSize, size, topSize);
    glVertex3f(topSize, size, topSize);

    // ---- Front face ----
    glColor3f(0.0f, 0.8f, 0.0f); // Front (Green)
    glVertex3f(topSize, size, topSize);
    glVertex3f(-topSize, size, topSize);
    glVertex3f(-bottomSize, -size, bottomSize);
    glVertex3f(bottomSize, -size, bottomSize);

    // ---- Back face ----
    glColor3f(0.0f, 0.7f, 0.7f); // Back (Blue)
    glVertex3f(bottomSize, -size, -bottomSize);
    glVertex3f(-bottomSize, -size, -bottomSize);
    glVertex3f(-topSize, size, -topSize);
    glVertex3f(topSize, size, -topSize);

    // ---- Left face ----
    glColor3f(1.0f, 1.0f, 0.0f);
    glVertex3f(-topSize, size, topSize);
    glVertex3f(-topSize, size, -topSize);
    glVertex3f(-bottomSize, -size, -bottomSize);
    glVertex3f(-bottomSize, -size, bottomSize);

    // ---- Right face ----
    glColor3f(0.5f, 0.6f, 0.6f); // Right (Darker Cyan)
    glVertex3f(topSize, size, -topSize);
    glVertex3f(topSize, size, topSize);
    glVertex3f(bottomSize, -size, bottomSize);
    glVertex3f(bottomSize, -size, -bottomSize);
    glEnd();

    // ---- Checkerboard Bottom Face ----
    int checkCount = 20;
    float tileSize = (2 * bottomSize) / checkCount;

    for (int i = 0; i < checkCount; i++) {
        for (int j = 0; j < checkCount; j++) {
            bool isWhite = (i + j) % 2 == 0;
            glColor3f(isWhite ? 1.0f : 0.0f, isWhite ? 1.0f : 0.0f, isWhite ? 1.0f : 0.0f);

            float x1 = -bottomSize + i * tileSize;
            float z1 = -bottomSize + j * tileSize;
            float x2 = x1 + tileSize;
            float z2 = z1 + tileSize;

            glBegin(GL_QUADS);
            glVertex3f(x1, -size, z1);
            glVertex3f(x2, -size, z1);
            glVertex3f(x2, -size, z2);
            glVertex3f(x1, -size, z2);
            glEnd();
        }
    }
}

void drawStripedBall(float radius, int slices, int stacks)
{
    for (int i = 0; i < slices; i++)
    {
        float theta1 = (i * 2 * M_PI) / slices;
        float theta2 = ((i + 1) * 2 * M_PI) / slices;

        glBegin(GL_QUAD_STRIP);
        for (int j = 0; j <= stacks; j++)
        {
            float phi = (j * M_PI) / stacks;
            float y = radius * cos(phi);
            float r_sin_phi = radius * sin(phi);

            float x1 = r_sin_phi * cos(theta1);
            float z1 = r_sin_phi * sin(theta1);

            float x2 = r_sin_phi * cos(theta2);
            float z2 = r_sin_phi * sin(theta2);

            // Choose color based on hemisphere and slice parity
            if (j <= stacks / 2)
            {
                // Lower hemisphere
                if (i % 2 == 0)
                    glColor3f(0.0f, 1.0f, 0.0f); // Green
                else
                    glColor3f(1.0f, 0.0f, 0.0f); // Red
            }
            else
            {
                // Upper hemisphere
                if (i % 2 == 0)
                    glColor3f(1.0f, 0.0f, 0.0f); // Red
                else
                    glColor3f(0.0f, 1.0f, 0.0f); // Green
            }

            glVertex3f(x1, y, z1);
            glVertex3f(x2, y, z2);
        }
        glEnd();
    }
}

void animateBall()
{
    if (isPaused) return;

    if (!initialized) {
        float angleXZ = randf(0.0f, 2 * M_PI);
        float angleY  = randf(0.0f, M_PI); // Launch angle between 30°-60°

        vx = ballSpeed * cos(angleY) * cos(angleXZ);
        vz = ballSpeed * cos(angleY) * sin(angleXZ);
        vy = ballSpeed * sin(angleY);

        initialized = true;
    }

    ballX += vx * deltaTime;
    ballY += vy * deltaTime;
    ballZ += vz * deltaTime;
    
    vy += gravity * deltaTime;

    // Floor collision (exact bottom face at -20.0)
    if (ballY <= -10.0f + ballR) {
        ballY = -10.0f + ballR;
        vy = -vy * bounceFactor;

        if (fabs(vy) < 0.1f) vy = 0.0f;
    }

    // Ceiling collision (top face at +20.0)
    if (ballY >= 10.0f - ballR) {
        ballY = 10.0f - ballR;
        vy = -vy * bounceFactor;
    }

    // X-axis wall collision (-20.0 to +20.0)
    if (ballX <= -20.0f + ballR || ballX >= 20.0f - ballR) {
        vx = -vx * bounceFactor;
        ballX = (ballX <= -20.0f + ballR) ? -20.0f + ballR : 20.0f - ballR;
    }

    // Z-axis wall collision (-20.0 to +20.0)
    if (ballZ <= -20.0f + ballR || ballZ >= 20.0f - ballR) {
        vz = -vz * bounceFactor;
        ballZ = (ballZ <= -20.0f + ballR) ? -20.0f + ballR : 20.0f - ballR;
    }

    glutPostRedisplay();
}







void init()
{
    glClearColor(0, 0, 0, 1.0); // Background color
    glEnable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE); // Disable backface culling to render both sides
}

void reshapeListener(GLsizei width, GLsizei height)
{
    // Prevent division by zero
    if (height == 0)
        height = 1;

    // Calculate aspect ratio
    GLfloat aspect = (GLfloat)width / (GLfloat)height;

    // Set viewport to cover entire window
    glViewport(0, 0, width, height);

    // Set up perspective projection
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();

    // 45-degree field of view, aspect ratio, near and far clipping planes
    gluPerspective(70.0f, aspect, 0.1f, 100.0f);
}

void randomlySetBallPosition()
{
    /* pick raw random point … */
    float cx = randf(ballminC_XY, ballmaxC_XY);
    float cz = randf(ballminC_XY, ballmaxC_XY);


    /* … snap it to nearest tile centre (optional)       */
    ballX =floor(cx / tileSize) * tileSize;
    ballZ = floor(cz / tileSize) * tileSize;

    printf("ballX = %f, ballZ = %f\n", ballX, ballZ);

    ballY = -1.0f;
    initialized = false; // Reset initialization for new direction
    vx = 0.0f; vy = 0.0f; vz = 0.0f; // Reset velocity
}




void display()
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    gluLookAt(cameraX, cameraY, cameraZ,
        lookX, lookY, lookZ,
        upX, upY, upZ);

    drawCube(10.0f);
    // Translate inside the cube
    glPushMatrix();
    // randomlySetBallPosition();
    glTranslatef(ballX, ballY, ballZ);
    drawStripedBall(ballR, 24, 24);
    glPopMatrix();

    glutSwapBuffers();
}

void specialKeyListener(int key, int x, int y)
{
    float lx = lookX - cameraX;
    float ly = lookY - cameraY;
    float lz = lookZ - cameraZ;

    // Normalize look direction
    float len = sqrt(lx * lx + ly * ly + lz * lz);
    lx /= len;
    ly /= len;
    lz /= len;

    // Compute right direction (cross product of look and up)
    float rx = ly * upZ - lz * upY;
    float ry = lz * upX - lx * upZ;
    float rz = lx * upY - ly * upX;

    // Normalize right direction
    len = sqrt(rx * rx + ry * ry + rz * rz);
    rx /= len;
    ry /= len;
    rz /= len;

    switch (key)
    {
    case GLUT_KEY_UP: // Move forward
        cameraX += lx * moveSpeed;
        cameraY += ly * moveSpeed;
        cameraZ += lz * moveSpeed;

        lookX += lx * moveSpeed;
        lookY += ly * moveSpeed;
        lookZ += lz * moveSpeed;
        break;

    case GLUT_KEY_DOWN: // Move backward
        cameraX -= lx * moveSpeed;
        cameraY -= ly * moveSpeed;
        cameraZ -= lz * moveSpeed;

        lookX -= lx * moveSpeed;
        lookY -= ly * moveSpeed;
        lookZ -= lz * moveSpeed;
        break;

    case GLUT_KEY_LEFT: // Strafe left
        cameraX -= rx * moveSpeed;
        cameraY -= ry * moveSpeed;
        cameraZ -= rz * moveSpeed;

        lookX -= rx * moveSpeed;
        lookY -= ry * moveSpeed;
        lookZ -= rz * moveSpeed;
        break;

    case GLUT_KEY_RIGHT: // Strafe right
        cameraX += rx * moveSpeed;
        cameraY += ry * moveSpeed;
        cameraZ += rz * moveSpeed;

        lookX += rx * moveSpeed;
        lookY += ry * moveSpeed;
        lookZ += rz * moveSpeed;
        break;

    case GLUT_KEY_PAGE_UP: // Move up
        cameraX += upX * moveSpeed;
        cameraY += upY * moveSpeed;
        cameraZ += upZ * moveSpeed;

        lookX += upX * moveSpeed;
        lookY += upY * moveSpeed;
        lookZ += upZ * moveSpeed;
        break;

    case GLUT_KEY_PAGE_DOWN: // Move down
        cameraX -= upX * moveSpeed;
        cameraY -= upY * moveSpeed;
        cameraZ -= upZ * moveSpeed;

        lookX -= upX * moveSpeed;
        lookY -= upY * moveSpeed;
        lookZ -= upZ * moveSpeed;
        break;
    }

    glutPostRedisplay();
}

/* ---------- helper for axis-angle rotation ---------- */
void rotateVec(float& x, float& y, float& z,
    float ax, float ay, float az,
    float ang)
{
    /* Rodrigues’ formula – axis must be unit */
    float c = cosf(ang), s = sinf(ang);
    float dot = ax * x + ay * y + az * z;
    float nx = x * c + (ay * z - az * y) * s + ax * dot * (1.0f - c);
    float ny = y * c + (az * x - ax * z) * s + ay * dot * (1.0f - c);
    float nz = z * c + (ax * y - ay * x) * s + az * dot * (1.0f - c);
    x = nx; y = ny; z = nz;
}

void keyboardListener(unsigned char key, int, int)
{
    const float ang = 0.05f;                // rotation step (rad)

    /* current basis vectors */
    float lx = lookX - cameraX;
    float ly = lookY - cameraY;
    float lz = lookZ - cameraZ;

    /* right  =  look × up  (needed for pitch / roll) */
    float rx = ly * upZ - lz * upY;
    float ry = lz * upX - lx * upZ;
    float rz = lx * upY - ly * upX;

    /* normalise helper vectors */
    float len = sqrtf(lx * lx + ly * ly + lz * lz);
    lx /= len; ly /= len; lz /= len;

    len = sqrtf(rx * rx + ry * ry + rz * rz);
    rx /= len; ry /= len; rz /= len;

    switch (key)
    {
        /* ---------- yaw (around up) ---------- */
    case '1':  rotateVec(lx, ly, lz, upX, upY, upZ, +ang); break; // look-left
    case '2':  rotateVec(lx, ly, lz, upX, upY, upZ, -ang); break; // look-right

        /* ---------- pitch (around right) ---------- */
    case '3':  rotateVec(lx, ly, lz, rx, ry, rz, +ang),
        rotateVec(upX, upY, upZ, rx, ry, rz, +ang); break;  // look-up
    case '4':  rotateVec(lx, ly, lz, rx, ry, rz, -ang),
        rotateVec(upX, upY, upZ, rx, ry, rz, -ang); break;  // look-down

        /* ---------- roll (around look axis) ---------- */
    case '5':  rotateVec(upX, upY, upZ, lx, ly, lz, +ang); break;  // tilt CW
    case '6':  rotateVec(upX, upY, upZ, lx, ly, lz, -ang); break;  // tilt CCW
    case ' ':
        isPaused = !isPaused; // Toggle pause state
        break;
    case 'r':                      // reset position & velocity
        randomlySetBallPosition();
        break;  
    case '+':
        ballSpeed += 1.0f; // Increase speed
        printf("ballSpeed = %f\n", ballSpeed);
        break;
    case '-':
        if (ballSpeed > 1.0f)
            ballSpeed -= 1.0f; // Decrease speed
        printf("ballSpeed = %f\n", ballSpeed);
        break;
    default:   return;
    }

    /* rebuild look point from new direction */
    lookX = cameraX + lx;
    lookY = cameraY + ly;
    lookZ = cameraZ + lz;

    glutPostRedisplay();
}


int main(int argc, char** argv)
{
    srand(static_cast<unsigned>(time(nullptr)));
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(1200, 1000);
    glutInitWindowPosition(50, 50);
    glutCreateWindow("OpenGL 3D Drawing");

    init();
    glutDisplayFunc(display);
    glutReshapeFunc(reshapeListener);
    glutSpecialFunc(specialKeyListener);
    glutKeyboardFunc(keyboardListener);

    glutIdleFunc(animateBall);

    glutMainLoop();
    return 0;
}
