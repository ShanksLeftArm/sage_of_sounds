
def formatSecondsToTime(total_seconds: int) -> str:
    seconds = formatToTensPlaces(int(total_seconds % 60))
    minutes = formatToTensPlaces(int((total_seconds / 60) % 60))
    hours = int(total_seconds / 3600)
    if hours > 0:
        hours = formatToTensPlaces(hours)
        return f'{hours}:{minutes}:{seconds}'
    else:
        return f'{minutes}:{seconds}'
    
def formatToTensPlaces(num: int) -> str:
    return f'0{num}' if num < 10 else num