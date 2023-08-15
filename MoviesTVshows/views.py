from django.shortcuts import render
import requests
from django.http import JsonResponse

TMDB_API_KEY = '0a91ef6215e90b04a44b09adc36432e1'
BASE_URL = 'https://api.themoviedb.org/3'


def search(query, category='movie'):
    url = f"{BASE_URL}/search/{category}?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url)
    data = response.json()
    return data['results']


def get_cast(id, category='movie', top_billed=False):
    endpoint = "aggregate_credits" if category == "tv" else "credits"
    url = f"{BASE_URL}/{category}/{id}/{endpoint}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    cast_list = []
    for person in data['cast'][:5] if top_billed else data['cast']:
        actor_name = person['name']
        character_name = ', '.join([role['character'] for role in person.get('roles', [])]) if 'roles' in person else person.get('character', 'N/A')
        cast_list.append({'actor': actor_name, 'character': character_name})

    return cast_list




def home(request):
    title1 = ""
    title2 = ""
    common_cast = []
    top_billed_cast1 = []
    top_billed_cast2 = []

    if request.method == 'POST':
        title1 = request.POST.get('title1')
        category1 = request.POST.get('category1')
        title2 = request.POST.get('title2')
        category2 = request.POST.get('category2')

        title1_data = search(title1, category1)[0]
        title2_data = search(title2, category2)[0]

        top_billed_cast1 = get_cast(title1_data['id'], category1, top_billed=True)
        top_billed_cast2 = get_cast(title2_data['id'], category2, top_billed=True)

        full_cast1 = get_cast(title1_data['id'], category1)
        full_cast2 = get_cast(title2_data['id'], category2)

        common_cast = []
        for actor_info1 in full_cast1:
            for actor_info2 in full_cast2:
                if actor_info1['actor'] == actor_info2['actor']:
                    merged_actor_info = {
                        'actor': actor_info1['actor'],
                        'character1': actor_info1['character'],
                        'character2': actor_info2['character']
                    }
                    common_cast.append(merged_actor_info)
                    break

    return render(request, 'home.html', {
        'top_billed_cast1': top_billed_cast1,
        'top_billed_cast2': top_billed_cast2,
        'common_cast': common_cast,
        'title1': title1,
        'title2': title2
    })

def autocomplete(request):
    query = request.GET.get('term')
    category = request.GET.get('category', 'movie')
    titles = search(query, category)
    title_names = [title['title'] if category == 'movie' else title['name'] for title in titles]
    return JsonResponse(title_names, safe=False)

