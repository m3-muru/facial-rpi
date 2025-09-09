import json
import re


class DeviceUsageParser:
	@staticmethod
	def run_stats():
		with open("../log/device/device_tracing.json") as json_file:
			json_file.seek(0)
			entries_dump = json.load(json_file)

			total_entries = len(entries_dump)
			print(f'total_entries: {total_entries}')

			current_hw_id = entries_dump[0].get("hwid")
			stats_dict = {
				current_hw_id: {
					"count": 0,
					"name": current_hw_id
				}
			}

			# Check through each camera usage for the loaded hwid information to see if it changes
			# 	on different computer
			for entry in entries_dump:
				current_hw_id = entry.get("hwid")

				# If already exist in our dict, add 1 to count
				if stats_dict.get(current_hw_id):
					stats_dict.get(current_hw_id)["count"] += 1
				# Else create a new entry in dict
				else:
					stats_dict[current_hw_id] = {
						"count": 1,
						"name": current_hw_id
					}

			print(json.dumps(stats_dict, indent=4))

			total_entries_parsed = 0
			for value in stats_dict.values():
				total_entries_parsed += value.get("count")
			print(f'total_entries_parsed: {total_entries_parsed}')

	@staticmethod
	def extract_test():
		with open("../test_case/29-10-2021-run-2.txt") as file:
			file.seek(0)

			for i, entry in enumerate(file):
				if 'Authenticating..' in entry or 'Enrolling...' in entry or '---------->>' in entry:

					if 'Enrolling...' in entry:
						print('\n')

					print(entry.rstrip('\n'))

	@staticmethod
	def generate_results_from_run_stage():
		result = {
			'employee_id': [
				{
					"employee_id": "employee_id",
					'against': 'employee_id',
					'score': 'match_score'
				},
				{
					"employee_id": "employee_id",
					'against': 'employee_id',
					'score': 'match_score'
				}
			]
		}
		with open("../test_case/29-10-2021-run-1-stage-1.txt") as file:
			file.seek(0)
			employee_id = None
			result_list = None
			for i, entry in enumerate(file):
				# print(entry.rstrip('\n'))
				if 'Enrolling...' in entry:
					if result_list:
						result[employee_id] = result_list

					result_list = []

					employee_id = re.findall(r'Employee ID: \d+', entry)
					employee_id = employee_id[0].replace('Employee ID: ', '')

				if 'against' in entry:
					against = re.findall(r'against \d+', entry)[0]
					against = against.replace('against ', '')
					match_score = re.findall(r'score=\d+', entry)[0]
					match_score = match_score.replace('score=', '')
					temp_dict = {
						"employee_id": employee_id,
						"against": against,
						"match_score": match_score
					}
					result_list.append(temp_dict)

		print(json.dumps(result, indent=4))


def main():
	dt = DeviceUsageParser()
	# dt.run_stats()
	# dt.extract_test()
	dt.generate_results_from_run_stage()


if __name__ == "__main__":
	main()
