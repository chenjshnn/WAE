import os

root = "."


task_dict = {"0":"Sign-up","1":"Image_Gallery","2":"Log_in","3":"Preference_Setting","4":"Navigation_Drawer"}
dirs = os.listdir(root)
for dir in dirs:
	if os.path.isdir(os.path.join(root,dir)):
		tasks = os.listdir(dir)
		for task in tasks:
			current_path = os.path.join(root, dir, task)
			if os.path.isdir(current_path):
				name = ''
				result_file = os.path.join(current_path,'result.txt')
				with open(result_file,'r') as fr:
					for line in fr.readlines():
						if 'task_id' in line:
							task_id = line.strip().split("'")[1]
							name = task_dict[task_id]
				print("ren {} {}".format(current_path,name))
				os.system("ren {} {}".format(current_path,name))

