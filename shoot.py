import sys,random
import pygame
from pygame.locals import RESIZABLE,DOUBLEBUF,FULLSCREEN,K_ESCAPE,KEYDOWN,KEYUP,K_SPACE

#Find resolution of the monitor
pygame.init()#To avoid error with pygame.display.Info(): pygame.error: video system not initialized 
infoObject=pygame.display.Info()
width,height=infoObject.current_w,infoObject.current_h

screen=pygame.display.set_mode((width,height),DOUBLEBUF|FULLSCREEN)
clock=pygame.time.Clock()

all_sprites=pygame.sprite.Group()
star_sprites=pygame.sprite.Group()
enemy_fire=pygame.sprite.Group()
ship_fire=pygame.sprite.Group() 
explosion_sprites=pygame.sprite.Group()
background=pygame.Surface((width,height),FULLSCREEN)

class Ship(pygame.sprite.Sprite):
	def __init__(self,x,y,group,fire_group):
		super(Ship,self).__init__()
		self.good=pygame.image.load("assets/ship.png").convert_alpha()
		self.hit=pygame.image.load("assets/ship-hit.png").convert_alpha()
		self.image=self.good
		self.rect=self.image.get_rect()#always get rect staring at (0,0)
		self.rect.center=(x,y)
		self.add(group)
		self.impacted=False
		self.energy=100
		self.groups=group
		self.fire=False
		self.laser=False
		self.fire_group=fire_group
	def impact(self):
		self.impacted=True
		self.energy-=10
	def update(self):
		x,y=pygame.mouse.get_pos()
		self.rect.center=(x,y)
		if self.fire:
			self.laser=FighterLaser(x,y,self.fire_group)
		if self.energy<0:
			self.kill()

			#Expand the rectangle around ship for explosion size
			x0,y0=self.rect.topleft
			x1,y1=self.rect.bottomright
			x0-=10
			y0-=10
			x1+=10
			y1+=10

			for i in range(10):
				e=Explosion(random.randint(x0,x1),random.randint(y0,y1),self.groups)
				explosion_sprites.add(e)
			all_sprites.clear(screen, background)
			pygame.display.set_caption("Game Over")
		if self.impacted:
			self.image=self.hit
			self.impacted=False
		else:
			self.image=self.good

class Enemy(pygame.sprite.Sprite):
	def __init__(self, x,y,fighter,group,fire_group):
		super(Enemy,self).__init__()
		self.good=pygame.image.load("assets/enemy-small.png").convert_alpha()
		self.hit=pygame.image.load("assets/enemy-hit.png").convert_alpha()
		self.image=self.good
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
		self.add(group)
		self.fighter=fighter
		self.velocity=0
		self.main_laser_counter=0
		self.fire_group=fire_group
		self.laser= False
		self.impacted=False
		self.energy=200
		self.main_group=group
	def impact(self):
		self.impacted=True
		self.energy-=10
	def update(self):
		fx,fy=self.fighter.rect.center
		sx,sy=self.rect.center
		if self.energy<0:
			self.kill()

			#Expand the rectangle around enemy for explosion size
			x0,y0=self.rect.topleft
			x1,y1=self.rect.bottomright
			x0-=10
			y0-=10
			x1+=10
			y1+=10

			for i in range(25):
				e=Explosion(random.randint(x0,x1),random.randint(y0,y1),self.main_group)
				explosion_sprites.add(e)

		#Move closer to fighter ship to attack
		if sy>fy:
			self.velocity=-1
			self.main_laser_counter=0
		elif sy<fy:
			self.velocity=1
			self.main_laser_counter=0
		else:
			self.velocity=0
			if self.main_laser_counter!=30:
				self.main_laser_counter+=10
		sy+=self.velocity
		self.rect.center=sx,sy

		#If fighter dead, stop firing
		if not self.fighter.alive() and self.laser.alive():
			self.fire_group.kill()

		#If enemy and ship are in a line, start firing
		if self.fighter.alive():
			if not (self.laser and self.laser.alive()):
				if self.main_laser_counter==30:
					self.laser=EnemyLaser(sx,sy,self.fire_group)

		if self.impacted:
			self.image=self.hit
			self.impacted=False
		else:
			self.image=self.good
		

class EnemyLaser(pygame.sprite.Sprite):
	def __init__(self,x,y,group):
		super(EnemyLaser,self).__init__()
		self.add(group)
		sheet=pygame.image.load("assets/laser.png").convert_alpha()
		# laser.png has 11 similarlaser images and dim=128x352 
		# i.e. Each laser has a dimension 128x32 since 352/11=32
		# Select a single laser image from the 11 images
		self.image=pygame.Surface((128,32),pygame.SRCALPHA).convert_alpha()
		self.image.blit(sheet,dest=(0,0),area=(0,0,128,32))
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
	def update(self):
		x,y=self.rect.center
		x+=50
		if x>width:
			self.kill()
		self.rect.center=x,y

class FighterLaser(pygame.sprite.Sprite):
	def __init__(self,x,y,group):
		super(FighterLaser,self).__init__()
		self.add(group)
		sheet=pygame.image.load("assets/hero-laser.png").convert_alpha()
		#select one laser image from the 11 images in the hero-laser.png
		self.image=pygame.Surface((64,16),pygame.SRCALPHA).convert_alpha()
		self.image.blit(sheet,dest=(0,0),area=(0,0,64,16))
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
	def update(self):
		x,y=self.rect.center
		x-=75 # longer distance than enemy laser to give a 'innocent' effect 
		if x<0:
			self.kill()
		self.rect.center=x,y

class Explosion(pygame.sprite.Sprite):
	def __init__(self,x,y,group):
		super(Explosion,self).__init__()
		self.add(group)
		sheet=pygame.image.load("assets/explosion_strip16.png").convert_alpha()
		self.images=[]
		self.index=0
		# explosion_strip16.png has dimension 1536x96 has 16 stages of explosion of same size
		# Cut each stage and place those 16 images into self.images[]
		for i in range(0,1536,96):
			# Each stage has dimension 96x96 since 1536/16=96
			img =pygame.Surface((96,96),pygame.SRCALPHA).convert_alpha()
			img.blit(sheet,dest=(0,0),area=(i,0,i+96,96))
			self.images.append(img)
		self.image=self.images[-1]
		self.rect=self.image.get_rect()
		self.rect.center=x,y
		self.delay=random.randint(1,15)
	def update(self):
		self.delay-=1
		if self.delay<=0:
			self.image=self.images[self.index]
			self.index+=1
			self.index%=len(self.images)
			if self.index==0:
				self.kill()

class Stardust(pygame.sprite.Sprite):
	def __init__(self,x,y,velocity,colour,group):
		super(Stardust,self).__init__()
		self.image=pygame.Surface((2,2))
		self.image.fill((colour,colour,colour))
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
		self.add(group)
		self.velocity=velocity
	def update(self):
		x,y=self.rect.center
		if x>width:
			x=0
		x+=self.velocity
		self.rect.center=x,y

def splashscreen():
	pygame.mouse.set_visible(False)
	intro = True
	while intro:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()

		screen.fill((0,0,0))
		bg=pygame.image.load("assets/bg.jpg")
		scaled_bg = pygame.transform.scale(bg, (width, height))
		screen.blit(scaled_bg,[0,0])
		font = pygame.font.Font(None,155)
		text = font.render("SPACE SHOOT", True, (255,255,255))
		text_rect = text.get_rect()
		text_x = width / 2 - text_rect.width / 2
		text_y = height / 2 - text_rect.height / 2
		screen.blit(text, [text_x, text_y])

		pygame.display.flip()
		pygame.time.delay(3000)
		screen.fill((0,0,0))
		intro=False

def parallax():
	#Creating parallax in stardust with different velocities and white/gray shades
	for i in range(500):
		x=random.randint(0,width)
		y=random.randint(0,height)
		s1=Stardust(x,y,1,100,all_sprites)
		star_sprites.add(s1)
	for i in range(500):
		x=random.randint(0,width)
		y=random.randint(0,height)
		s2=Stardust(x,y,2,150,all_sprites)
		star_sprites.add(s2)
	for i in range(500):
		x=random.randint(0,width)
		y=random.randint(0,height)
		s3=Stardust(x,y,3,255,all_sprites)
		star_sprites.add(s3)
	star_sprites.draw(screen)

def menu():
	pygame.mouse.set_visible(True)
	screen.fill((0,0,0))
	parallax()

	font=pygame.font.Font(None,50)
	text = font.render("SPACE SHOOT", True, (255,255,255,125))
	text_rect = text.get_rect()
	text_x = width / 4 - text_rect.width / 2
	text_y = height / 2 - text_rect.height / 2
	screen.blit(text, [text_x, text_y])

	while True:
		button("SHOOT!",int (width/2),int(height/4),int(width/4),int(height/8),(255,255,255),(150,150,150),game)
		button("QUIT",int (width/2),int(height/2),int(width/4),int(height/8),(255,255,255),(150,150,150),quit)
		pygame.display.flip()
		for event in pygame.event.get():
			if event.type==KEYDOWN:
				if event.key==K_ESCAPE:
					print("Thanks for playing!")
					sys.exit(0)

def button(msg,x,y,w,h,ic,ac,action=None):
	mouse = pygame.mouse.get_pos()
	click = pygame.mouse.get_pressed()
	if x+w > mouse[0] > x and y+h > mouse[1] > y:
		pygame.draw.rect(screen, ac,(x,y,w,h))
		if click[0] == 1 and action != None:
			action()
	else:
		pygame.draw.rect(screen, ic,(x,y,w,h))

	font = pygame.font.SysFont("comicsansms",20)
	text = font.render(msg, True,(0,0,0))
	text_rect = text.get_rect()
	text_x = x+(w/2) - text_rect.width / 2
	text_y = y+(h/2) - text_rect.height / 2
	screen.blit(text, [text_x, text_y])

def quit():
	print("Thanks for playing!")
	sys.exit(0)

def game():
	screen.fill((0,0,0))

	parallax()

	fighter=Ship(width/2,height/2,all_sprites,[all_sprites,ship_fire])
	enemy=Enemy(width/3,height/2,fighter,all_sprites,[all_sprites,enemy_fire])
	gameover=False
	pygame.mouse.set_visible(False)

	while not gameover:
		clock.tick(20)
		for event in pygame.event.get():
			if event.type==KEYDOWN:
				if event.key==K_ESCAPE:
					menu()
				if event.key==K_SPACE:
					fighter.fire=True
			elif event.type==KEYUP:
				if event.key==K_SPACE:
					fighter.fire=False

		#Check if fighter collided with enemy's fire
		collided=pygame.sprite.spritecollideany(fighter,enemy_fire)
		if collided:
			collided.kill()
			fighter.impact()

		#Check if enemy collided with fighter's fire 
		collided=pygame.sprite.spritecollideany(enemy,ship_fire)
		if collided:
			collided.kill()
			enemy.impact()

		all_sprites.clear(screen,background)
		all_sprites.update()# call self.update() with all member sprites
		all_sprites.draw(screen)#uses self.image and self.rect
		pygame.display.flip()
		if (not fighter.alive() or not enemy.alive()) and len(explosion_sprites)==0:

			if not fighter.alive():
				DisplayText("GAME OVER")
			else:
				DisplayText("WELL DONE")

def DisplayText(win_or_dead):
	# If game over is true, draw game over
	all_sprites.clear(screen,background)
	all_sprites.update()# call self.update() with all member sprites
	all_sprites.draw(screen)#uses self.image and self.rect
	pygame.display.flip()

	#Place Game Over at Centre
	font=pygame.font.Font(None,50)
	text = font.render(win_or_dead, True, (255,255,255))
	text_rect = text.get_rect()
	text_x = width / 2 - text_rect.width / 2
	text_y = height / 2 - text_rect.height / 2
	screen.blit(text, [text_x, text_y])
	pygame.display.flip()
	pygame.time.delay(3000)
	menu()

splashscreen()
menu()
#game()
