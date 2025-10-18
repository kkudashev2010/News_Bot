import http.client

conn = http.client.HTTPSConnection("booking-com15.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "6e546ecd12msh242fc058d6df145p1ec861jsn246f46226a01",
    'x-rapidapi-host': "booking-com15.p.rapidapi.com"
}


def get_dest_id(city:str):
    conn.request("GET", f"/api/v1/hotels/searchDestination?query={city}", headers=headers)

    res = conn.getresponse()
    data = res.read()
    print(type(data))

    print(data.decode("utf-8"))

if __name__ == '__main__':
    get_dest_id('London')
