from enum import Enum


class GestureDetectionStatus(Enum):
    INDEXFINGER = 1
    VSIGN = 2

    # https://stackoverflow.com/a/65225753/11537143
    @staticmethod
    def is_valid_enum(gesture_detection_status):
        try:
            GestureDetectionStatus(gesture_detection_status)
        except ValueError:
            return False
        return True

    @staticmethod
    def get_str(gesture_detection_status):
        if GestureDetectionStatus.is_valid_enum(gesture_detection_status):
            return gesture_detection_status.name
        else:
            return "Invalid enum status provided, unable to fetch name"


def main():
    print(GestureDetectionStatus.get_str(5))
    print(GestureDetectionStatus.is_valid_enum(6))

    print('Program ended..')


if __name__ == '__main__':
    main()
