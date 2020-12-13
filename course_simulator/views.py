from django.shortcuts import render, HttpResponseRedirect, reverse
from django.http import JsonResponse
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from .models import *
from background_task import background
from background_task.models import *
from django.contrib import messages
from django.conf import settings


def usis_login(browser, email, password):
	browser.get("http://usis.bracu.ac.bd/academia/")

	time.sleep(1)

	browser.find_element_by_id("username").send_keys(email)
	browser.find_element_by_id("password").send_keys(password)

	browser.find_element_by_id("ctl00_leftColumn_ctl00_btnLogin").click()


def login_confirmation(browser):
	browser.get("http://usis.bracu.ac.bd/academia/")

	time.sleep(1)

	if str(browser.current_url) == "http://usis.bracu.ac.bd/academia/dashBoard/show":
		print("Login successful")
		return True
	else:
		return False


def navigate_to_class_schedule(browser):
	anchors = browser.find_elements_by_tag_name("a")
	for anchor in anchors:
		try:
			if str(anchor.text) == "Student":
				anchor.click()
				break
		except Exception:
			pass

	time.sleep(1)

	anchors = browser.find_elements_by_tag_name("a")
	for anchor in anchors:
		try:
			if str(anchor.text) == "Show Class Schedule":
				anchor.click()
				break
		except Exception:
			pass

	print("Class schedule navigation successful")
	time.sleep(2)


def check_schedule_loaded(browser):
	return browser.find_element_by_id("academiaSession").is_displayed()


def load_courses(browser):
	browser.execute_script("$(\"#academiaSession\").append(new Option(\"Spring 2021\", \"627113\"))")
	time.sleep(1)
	browser.find_element_by_id("academiaSession").click()
	options = browser.find_elements_by_tag_name("option")
	for option in options:
		if option.text == "Spring 2021":
			option.click()
			break
	time.sleep(1)
	browser.find_element_by_id("load-button").click()

	time.sleep(5)

	browser.find_element_by_class_name("ui-pg-selbox").click()
	options = browser.find_elements_by_tag_name("option")
	for option in options:
		if option.text == "All":
			option.click()
			break

	print("Course loading successful")
	time.sleep(5)


def welcome(request):
	semester_list = []

	current_year = int(datetime.date.today().year)
	start_value = 627110

	for year in range(current_year, current_year + 2):
		for i in range(1, 4):
			if i == 1:
				semester_list.append(("Spring %i" % year, start_value))
			elif i == 2:
				semester_list.append(("Summer %i" % year, start_value))
			elif i == 3:
				semester_list.append(("Fall %i" % year, start_value))
			start_value += 1

	semester_list.reverse()

	context = {
		'semester_list': semester_list
	}

	return render(request, 'course_simulator/welcome.html', context)


@background(schedule=20)
def updateDBBackground(data):
	chrome_options = Options()
	chrome_options.add_argument("--headless")

	if settings.DEVELOPMENT:
		browser_instance = webdriver.Chrome('./chromedriver_linux', options=chrome_options)
	else:
		browser_instance = webdriver.Chrome('/home/usissim.com/public_html/chromedriver_linux', options=chrome_options)

	time.sleep(1)

	attempt = 0

	log_instance = UpdateLog.objects.create(updated_by=data['username'])

	try:
		usis_login(browser_instance, data['username'], data['password'])

		while True:
			if attempt == 5:
				break

			if login_confirmation(browser_instance):
				break
			else:
				attempt += 1
				usis_login(browser_instance, data['username'], data['password'])
	except Exception:
		log_instance.update_status = "Failed"
		log_instance.save()
		print("Login Failed!")
		browser_instance.close()

	if attempt < 3:
		try:
			navigate_to_class_schedule(browser_instance)
		except Exception:
			log_instance.update_status = "Failed"
			log_instance.save()
			print("Navigate to class schedule failed!")
			browser_instance.close()

		while True:
			if check_schedule_loaded(browser_instance):
				break
			else:
				time.sleep(1)

		try:
			load_courses(browser_instance)
		except Exception:
			log_instance.update_status = "Failed"
			log_instance.save()
			print("Course loading failed!")
			browser_instance.close()

		try:
			rows = browser_instance.find_elements_by_tag_name("tr")
			if len(rows) > 5:
				CourseList.objects.all().delete()
			for row in rows:
				courses = row.find_elements_by_tag_name("td")
				if len(courses) > 5:
					# print(len(courses))
					if str(courses[0].text) != "":
						try:
							CourseList.objects.create(
								semester=str(data["semester"]),
								course_code=str(courses[1].text) + "\n(" + str(courses[2].get_attribute('title')) + ")",
								section=int(courses[3].text),
								total_seat=int(courses[4].text),
								faculty=str(courses[6].text),
								instructor=str(courses[8].text) + "\n(" + str(courses[7].get_attribute('title')) + ")",
								exam_date=str(courses[9].text),
								exam_time=str(courses[10].text),
								sunday=str(courses[11].text),
								monday=str(courses[12].text),
								tuesday=str(courses[13].text),
								wednesday=str(courses[14].text),
								thursday=str(courses[15].text),
								friday=str(courses[16].text),
								saturday=str(courses[17].text)
							)
						except Exception:
							pass
			log_instance.update_status = "Successful"
			log_instance.save()
		except Exception:
			log_instance.update_status = "Failed"
			log_instance.save()
			print("Course parsing failed!")
			browser_instance.close()
	else:
		log_instance.update_status = "Failed"
		log_instance.save()
		print("Failed")

	time.sleep(5)

	browser_instance.close()


def updateDB(request):
	if request.method == "POST":
		if UpdateLog.objects.filter(update_status="Processing").exists():
			instance = UpdateLog.objects.filter(update_status="Processing")
			for log in instance:
				log.update_status = "Cancelled"
				log.save()
		updateDBBackground({"semester": request.POST['semester'], "username": request.POST['username'],
							"password": request.POST['password']})
		messages.add_message(request, messages.SUCCESS, "Task is scheduled to be executed within next 10 minutes.")
		return HttpResponseRedirect(reverse('welcome'))

	if 'semester' in request.GET:
		update_log = UpdateLog.objects.all().order_by('-updated_at')
		queue_log = Task.objects.filter(attempts=0)

		context = {
			'update_log': update_log,
			'queue_log': queue_log,
			'semester': request.GET['semester']
		}

		return render(request, 'course_simulator/update_db.html', context)
	else:
		return HttpResponseRedirect(reverse('welcome'))


def coursesPage(request):
	if 'semester' in request.GET and 'name' in request.GET:
		courses = CourseList.objects.filter(semester=request.GET['semester'])
		context = {
			'semester': request.GET['semester'],
			'name': request.GET['name'],
			'courses': courses
		}
		return render(request, 'course_simulator/courses.html', context)
	else:
		return HttpResponseRedirect(reverse('welcome'))


def coursesView(request):
	# Get the data from request
	search_value = request.GET['search[value]'].strip()
	startLimit = int(request.GET['start'])
	endLimit = startLimit + int(request.GET['length'])
	data_array = []

	# Count the total length
	totalLength = CourseList.objects.count()

	# if search parameter is passed
	if search_value != '':
		# Querying dataset
		dataList = CourseList.objects.filter(
			Q(course_code__contains=search_value) | Q(course_code__contains=str(search_value).upper()) | Q(
				course_code__contains=str(search_value).lower()) | Q(instructor__contains=search_value) | Q(
				instructor__contains=str(search_value).lower()) | Q(instructor__contains=str(search_value).upper()) |
			Q(faculty__contains=search_value) | Q(faculty__contains=str(search_value).lower()) | Q(
				faculty__contains=str(search_value).upper()))

		# Filtering dataset
		dataFilter = dataList[startLimit:endLimit]

		# Get the filter length
		filterLength = dataList.count()
	else:
		# Querying dataset
		dataList = CourseList.objects.all()

		# Filtering dataset
		dataFilter = dataList[startLimit:endLimit]

		# Get the filter length
		filterLength = totalLength

	indexCount = startLimit + 1

	# Processing the data for table
	for key, item in enumerate(dataFilter):
		date = item.exam_date
		if str(date).strip() != "":
			dateTimeStr = datetime.datetime.strptime(date, "%d-%m-%Y")
			date = datetime.date(int(dateTimeStr.year), int(dateTimeStr.month), int(dateTimeStr.day)).strftime(
				"%d %B %Y")
		exam = date + "\n" + item.exam_time
		row_array = [indexCount, item.course_code, item.section, item.total_seat, item.faculty, item.instructor,
					 exam, item.sunday, item.monday, item.tuesday, item.wednesday, item.thursday, item.friday,
					 item.saturday]
		data_array.append(row_array)
		indexCount += 1

	# Preparing the response
	response = {
		"draw": request.GET['draw'],
		"recordsTotal": totalLength,
		"recordsFiltered": filterLength,
		"data": data_array
	}

	# Returning json response
	return JsonResponse(response)


def courseSession(request):
	if 'course_array' in request.POST:
		request.session['course_array'] = request.POST['course_array']
	return JsonResponse({"error": False})
