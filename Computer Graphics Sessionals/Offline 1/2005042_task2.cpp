#include<stdio.h>
#include<stdlib.h>
#include<math.h>
#include <time.h> 
#include <sys/time.h>
#include <GL/glut.h> // GLUT, includes glu.h and gl.h

#define pi (2*acos(0.0))

struct point
{
	double x,y,z;
};
void drawCircle(double radius,int segments,double color_red,double color_green,double color_blue)
{
    int i;
    struct point points[101];
    glColor3f(color_red,color_green,color_blue);
    //generate points
    for(i=0;i<=segments;i++)
    {
        points[i].x=radius*cos(((double)i/(double)segments)*2*pi);
        points[i].y=radius*sin(((double)i/(double)segments)*2*pi);
    }
    //draw segments using generated points
    for(i=0;i<segments;i++)
    {
        glBegin(GL_LINES);
        {
            glVertex3f(points[i].x,points[i].y,0);
            glVertex3f(points[i+1].x,points[i+1].y,0);
        }
        glEnd();
    }
}

void drawMarkers()
{
    double outerR = 0.9;          // where the tick touches the rim
    double hour_tick = 0.75;         // length of an hour tick
    double min_tick  = 0.80;         // length of a minute tick

    for (int i = 0; i < 60; ++i)
    {
        double a = 2.0 * pi * i / 60.0;       // angle for this tick
        double xOut = (i%15!=0) ? outerR * cos(a) : outerR * 0.90 * cos(a); // hour ticks are shorter
        double yOut = (i%15!=0) ? outerR * sin(a) : outerR * 0.90 * sin(a); // hour ticks are shorter

        double innerR = (i % 5 == 0) ? hour_tick : min_tick;   // long vs short tick
        glLineWidth((i % 5 == 0) ? 10 : 1);               // thicker hour ticks
        double xIn  = innerR * cos(a);
        double yIn  = innerR * sin(a);

        glBegin(GL_LINES);
            glVertex2f(xIn,  yIn);
            glVertex2f(xOut, yOut);
        glEnd();
    }

    glLineWidth(1);   // restore default
}


void drawHand(double angleRad, double length, double thickness,double red, double green, double blue)
{
    glColor3f(red, green, blue);
    glLineWidth(thickness);

    glBegin(GL_LINES);
        glVertex2f(0.0, 0.0);
        glVertex2f(length * cos(angleRad), length * sin(angleRad));
    glEnd();

    glPushMatrix();
        glTranslatef(0.95 * cos(angleRad), 0.95 * sin(angleRad), 0); // move to tip
        glRotatef((angleRad * 180.0/pi) - 90, 0, 0, 1);  // optional: align if needed
        glScalef(0.02, 0.02, 0);  // scale the square to make it small
        glBegin(GL_QUADS);
            glVertex2f( 1,  1);
            glVertex2f( 1, -1);
            glVertex2f(-1, -1);
            glVertex2f(-1,  1);
        glEnd();
    glPopMatrix();

    glLineWidth(1);
}

void drawClockHands()
{
    /* Get more precise current time */
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *tm = localtime(&tv.tv_sec);

    int hour = tm->tm_hour % 12;
    int min  = tm->tm_min;
    int sec  = tm->tm_sec;
    int millis = tv.tv_usec / 1000;    // microseconds → milliseconds

    /* Compute smooth angles */
    double smoothSec = sec + millis / 1000.0;
    double smoothMin = min + smoothSec / 60.0;
    double smoothHour = hour + smoothMin / 60.0;

    double secAngle  = pi/2 - (smoothSec  * 2.0 * pi / 60.0);
    double minAngle  = pi/2 - (smoothMin  * 2.0 * pi / 60.0);
    double hourAngle = pi/2 - (smoothHour * 2.0 * pi / 12.0);

    /* Draw hands */
    drawHand(hourAngle, 0.4, 8, 1, 1, 1); // hour hand
    drawHand(minAngle,  0.6, 4, 1, 1, 1); // minute hand
    drawHand(secAngle,  0.75, 2, 1, 0, 0); // second hand
}


void drawCenterDot()
{
    double radius = 0.02;
    int segments = 20;

    glColor3f(1, 1, 1); // black dot
    glBegin(GL_POLYGON);
    for (int i = 0; i < segments; i++) {
        double angle = 2.0 * pi * i / segments;
        double x = radius * cos(angle);
        double y = radius * sin(angle);
        glVertex2f(x, y);
    }
    glEnd();
}

void reshapeListener(GLsizei w, GLsizei h)
{
    if(h == 0) h = 1;                   // protect /0
    glViewport(0, 0, w, h);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();

    double aspect = (double)w / h;
    if (aspect >= 1.0)
        gluOrtho2D(-aspect, aspect, -1, 1); // widen X when window is wide
    else
        gluOrtho2D(-1, 1, -1/aspect, 1/aspect); // enlarge Y when window is tall
}
void drawText(const char *text, float x, float y)
{
    glRasterPos2f(x, y);
    for (int i = 0; text[i] != '\0'; i++)
    {
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, text[i]);
    }
}
void drawNumbers()
{
    glColor3f(1, 1, 1); // white color for numbers

    // Positions slightly inside the clock rim
    drawText("12", -0.04f, 0.83f);
    drawText("3",  0.85f, -0.04f);
    drawText("6", -0.02f, -0.88f);
    drawText("9", -0.88f, -0.04f);
}


void update(int value)
{
    glutPostRedisplay();           // Ask OpenGL to redraw the scene
    glutTimerFunc(10, update, 0);   // Set timer again to call after 30ms
}

void init() {
    glClearColor(0, 0, 0, 0);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluOrtho2D(-1, 1, -1, 1); // 2D Orthographic Projection
}

void display() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    // glClearColor(0, 0, 0, 0);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    drawCircle(0.9f, 100,0,1,1);
    drawCircle(0.95f, 100,1,0,0); 
    drawMarkers();
    drawNumbers();
    drawClockHands();
    drawCenterDot();

    glutSwapBuffers();
}




int main(int argc, char **argv) {
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(1000, 800);
    glutInitWindowPosition(800, 100);
    glutCreateWindow("Analog Clock ");
    glutReshapeFunc(reshapeListener);

    init();

    glutDisplayFunc(display);
    glutTimerFunc(10, update, 0);

    glutMainLoop();
    return 0;
}
