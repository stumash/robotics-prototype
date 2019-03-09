############################################################
############SCRB 2019 INVERSE KINEMATICS PACKAGE############
############################################################

#NOTE: The first angle in the code (a1a) is the angle that the base makes
#with the horizontal. Since the base is immobile, this angle is assumed to
#be constant. In fact, the properties of the base are not taken into
#account in this code but are simply added to the final figure.
#For this reason, each angle has a higher coefficient than its
#corresponding link. E.g. link 1 corresponds to angle computed_proximal_angle.

#This code uses a closed form solution to determine the orientation of the
#joints of a planar RRR arm for its end effector to reach a given point.For
#more information about workings of the code, contact Maxim Kaller.

import math
import pygame


############MANIPULATOR PHYSICAL PARAMETERS############


#LENGTHS:
rover_height = 0.366 #m
base_length = 0.103 #m
proximal_length = 0.413 #m
distal_length = 0.406 #m
wrist_length = 0.072 + 0.143 #m (until tip of fingers)
length_array = [proximal_length, distal_length, wrist_length]

#ANGLES (IN RADIANS):
proximal_max_angle = math.pi
proximal_min_angle = -math.pi
distal_max_angle = math.pi
distal_min_angle = -math.pi
wrist_max_angle = math.pi
wrist_min_angle = -math.pi
minmax = [[0,0], [proximal_min_angle,proximal_max_angle], [distal_min_angle, distal_max_angle], [wrist_min_angle, wrist_max_angle]]

#INITIALIZE GLOBAL VARIABLES
computed_angles = [0, proximal_min_angle, distal_min_angle, wrist_min_angle]
sample_size = 50

###################PYGAME PARAMETERS###################
Window_X = 640
Window_Y = 480

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
BLUE =  (  0,   0, 255)
GREEN = (  0, 255,   0)
RED =   (255,   0,   0)

###############PYGAME FUNCTIONS###############
def draw(self, pts):
	for i in range(pts):
		pygame.draw.line(self.screen, self.color, self.projected_position[i][0], self.projected_position[i][1], self.width)


def drawText(screen, text, color, pos):
	font = pygame.font.Font(None, 36)
	text_surface = font.render(text, True, color)
	screen.blit(text_surface, pos)

def GenerateRepresentativeCoordinates(PointArray, offset_x, offset_y, size = 4):
	Scale_Factor = 0.5

	if size is 0:
		resized_array = [0,0]
		resized_array[0] = int(PointArray[0] * Window_X * Scale_Factor + offset_x)
		resized_array[1] = int(- PointArray[1] * Window_Y * Scale_Factor + offset_y)

	else:
		resized_array = [ [[0,0],[0,0]] for x in range(size)]
		for i in range(0,size):
			resized_array[i][0][0] = PointArray[i][0][0] * Window_X * Scale_Factor + offset_x
			resized_array[i][0][1] = PointArray[i][0][1] * Window_Y * Scale_Factor + offset_y
			resized_array[i][1][0] = PointArray[i][1][0] * Window_X * Scale_Factor + offset_x
			resized_array[i][1][1] = PointArray[i][1][1] * Window_Y * Scale_Factor + offset_y

	return resized_array


################PYGAME CLASSES################
class ProjectionView:
	def __init__(self, color, X, Y, screen, actual_position = 0, projected_position = 0, width = 6, font = 'verdana12'):
		self.color = color
		self.width = width
		self.X = X
		self.Y = Y
		self.screen = screen
        #MISSING FUNCTIONALITY FOR X AND Y



#######################FUNCTIONS#######################


def ComputeWorkspace(joint_array, joint_num,minmax_array, length_array):
	global sample_size

	for j1 in range(minmax_array[0][0],minmax_array[0][1], (minmax_array[0][1] - minmax_array[0][0])/sample_size):
		for j2 in range(minmax_array[1][0],minmax_array[1][1], (minmax_array[1][1] - minmax_array[1][0])/sample_size):
			for j3 in range(minmax_array[2][0],minmax_array[2][1], (minmax_array[2][1] - minmax_array[2][0])/sample_size):
				pt[ sample_size * sample_size * j1 + sample_size * j2 + j3][0] = length_array[0] * math.cos(j1) + length_array[1] * math.cos(j2) + length_array[2] * math.cos(j3)
				pt[ sample_size * sample_size * j1 + sample_size * j2 + j3][1] = length_array[0] * math.sin(j1) + length_array[1] * math.sin(j2) + length_array[2] * math.sin(j3)
	return pt



def ComputeIK(X, Y, Z):

	global computed_angles
	solution_angles = [[0,0,0,0], [0,0,0,0]]
	solution_usable = [True, True]

	#Base rotation CALCULATION
	solution_angles[0][0] = solution_angles[1][0] = math.atan( Z/X )
	R = math.sqrt( pow(X,2) + pow(Z,2) )

	#Check to see if point is too far
	#REPLACE LATER WITH FANCIER SHIT
	beta = math.atan2(Y - base_length , R) #Calculates beta, which is the sum of the angles of all links
	Wrist_X = R - wrist_length * math.cos(beta) #Calculates wrist X coordinate
	Wrist_Y = (Y - base_length) - wrist_length * math.sin(beta) #Calculates wrist Y coordinate

	if math.sqrt(pow(Wrist_X,2) + pow(Wrist_Y,2)) > proximal_length + distal_length:
		print('ERROR: SET POINT BEYOND ARM WORKSPACE')
		return 0


	cosine_distal_angle = (pow(Wrist_X,2) + pow(Wrist_Y,2) - pow(proximal_length,2) - pow(distal_length,2))/(2 * proximal_length * distal_length)
	solution_angles[0][2] = math.acos(cosine_distal_angle)
	solution_angles[1][2] = -solution_angles[0][2]


	#Calculate phi: Angle between tangent line and proximal link
	aphi = (pow(Wrist_X,2) + pow(Wrist_Y,2) + pow(proximal_length,2) - pow(distal_length,2))/(2 * math.sqrt(pow(Wrist_X,2) + pow(Wrist_Y,2)) * proximal_length)
	phi = math.acos(aphi)

	#Depending on the configuration of the arm, phi and beta can be used to
	#find the second angle

	if solution_angles[0][2] <= 0:
		solution_angles[0][1] = beta + phi
		solution_angles[1][1] = beta - phi
	else:
		solution_angles[0][1] = beta - phi
		solution_angles[1][1] = beta + phi

	#WRIST ANGLE CALCULATION: REPLACE WITH FANCY SHIT LATER
	solution_angles[0][3] = beta - (solution_angles[0][1] + solution_angles[0][2])
	solution_angles[1][3] = beta - (solution_angles[1][1] + solution_angles[1][2])


	#ELIMIATION OF ONE OF THE ANGLE SETS

	for i in range(1,4):
		if solution_angles[0][i] > minmax[i][1] or solution_angles[0][1] < minmax[i][0]:
			solution_usable[0] = False
			solution = 1
			print('One Solution is not possible')
		if solution_angles[1][i] > minmax[i][1] or solution_angles[1][1] < minmax[i][0]:
			solution_usable[1] = False
			solution = 0
			print('One Solution is not possible')

	if (solution_usable[0] is False) and (solution_usable[1] is False):
		print('Error: No arm configuration available for specified set point')
		return 0

	elif (solution_usable[0] is True) and (solution_usable[1] is True):
		error0 = pow(solution_angles[0][1] - computed_angles[1],2) + pow(solution_angles[0][2] - computed_angles[2],2) + pow(solution_angles[0][3] - computed_angles[3],2)
		error1 = pow(solution_angles[1][1] - computed_angles[1],2) + pow(solution_angles[1][2] - computed_angles[2],2) + pow(solution_angles[1][3] - computed_angles[3],2)
		if error0 > error1:
			solution = 1

		else:
			solution = 0

	return solution_angles[solution]


def UpdateArmSideValues(angles):

	base_start_point = [0,0]
	base_end_point = [base_start_point[0], base_start_point[1] - base_length]
	proximal_start_point = base_end_point
	proximal_end_point =  [proximal_start_point[0] + proximal_length * math.cos(angles[1]) , proximal_start_point[1] - proximal_length * math.sin(angles[1])]
	distal_start_point = proximal_end_point
	distal_end_point =  [distal_start_point[0] + distal_length * math.cos(angles[1] + angles[2]) , distal_start_point[1] - distal_length * math.sin(angles[1] + angles[2])]
	wrist_start_point = distal_end_point
	wrist_end_point = [wrist_start_point[0] + wrist_length * math.cos(angles[1] + angles[2] + angles[3]) , wrist_start_point[1] - wrist_length * math.sin(angles[1] + angles[2] + angles[3])]

	return [ [base_start_point, base_end_point], [proximal_start_point, proximal_end_point], [distal_start_point, distal_end_point] , [wrist_start_point, wrist_end_point] ]

def UpdateArmTopValues(angles):
	arm_start_point = [0,0]
	arm_radius = proximal_length * math.cos(angles[1]) + distal_length * math.cos(angles[1] + angles[2]) + wrist_length * math.cos(angles[1] + angles[2] + angles[3])
	arm_end_point = [arm_radius * math.cos(angles[0]), -arm_radius * math.sin(angles[0])]

	return [[arm_start_point, arm_end_point]]

#########################MAIN#########################

#################PYGAME INIT#################
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((Window_X,Window_Y))
pygame.display.set_caption("Inverse Kinematics Module")
mode = 1

Sideview = ProjectionView(RED, Window_X/4, 3*Window_Y/4, screen)
Topview = ProjectionView(RED, 3*Window_X/4, Window_Y/4, screen)

done = False
clock = pygame.time.Clock()

#################PYGAME LOOP#################
while not done:

	#Check if user closed window
    clock.tick(10)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done=True

	#Update arm view
    screen.fill(WHITE)

	#INVERSE KINEMATICS MODE
    if mode is 1:
    	set_point = [0.3,0.7,0.4]
    	set_point_2D = [math.sqrt( pow(set_point[0],2) + pow(set_point[2],2) ), set_point[1]]
    	top_point = [set_point[0], set_point[2]]
    	computed_angles = ComputeIK(set_point[0], set_point[1], set_point[2])

		#Sideview
    	Sideview.actual_position = UpdateArmSideValues(computed_angles)
    	Sideview.projected_position = GenerateRepresentativeCoordinates(Sideview.actual_position, Sideview.X, Sideview.Y)
    	draw(Sideview, 4)
    	pygame.draw.circle(screen, RED, [int(Sideview.projected_position[0][0][0]),int(Sideview.projected_position[0][0][1])] , 10)
    	drawText(screen, "Side View", BLACK, [Sideview.X, Sideview.Y + 50])



		#Topview
    	Topview.actual_position = UpdateArmTopValues(computed_angles)
    	Topview.projected_position = GenerateRepresentativeCoordinates(Topview.actual_position, Topview.X, Topview.Y, 1)
    	draw(Topview, 1)
    	pygame.draw.circle(screen, RED, [int(Topview.projected_position[0][0][0]),int(Topview.projected_position[0][0][1])] , 10)
    	drawText(screen, "Top View", BLACK, [Topview.X, Topview.Y + 50])

		#Draw a circle around target point
    	desired_side_point = GenerateRepresentativeCoordinates(set_point_2D , Sideview.X, Sideview.Y, 0)
    	pygame.draw.circle(screen, BLUE, desired_side_point , 15, 3)

    	desired_top_point = GenerateRepresentativeCoordinates(top_point , Topview.X, Topview.Y, 0)
    	pygame.draw.circle(screen, BLUE, desired_top_point , 15, 3)

	#WORKSPACE MODE
    if mode is 0:
    	for i in range(0, math.pow(sample_size,3) ):
    		pygame.draw.circle(screen, BLUE, desired_point , 1)


	#This is required to update the display
    pygame.display.flip()

pygame.quit()
