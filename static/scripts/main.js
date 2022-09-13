
function buy(appid)
{
    fetch("/buy/" + appid.toString(), { method: 'POST' })
        .then((response) => {
            return response.json();
        })
        .then((data) => {
            document.getElementById("buyButton").style.display = data['bought'] ? "none" : "block"
            document.getElementById("revertButton").style.display = data['bought'] ? "block" : "none"
        });
}

function revert(appid)
{
    fetch("/revert/" + appid.toString(), { method: 'POST' })
        .then((response) => {
            return response.json();
        })
        .then((data) => {
            document.getElementById("buyButton").style.display = data['bought'] ? "none" : "block"
            document.getElementById("revertButton").style.display = data['bought'] ? "block" : "none"
        });
}

function wishlist(appid, state)
{
    fetch("/wishlist/" + appid.toString(), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'state': state}) })
        .then((response) => {
            return response.json();
        })
        .then((data) => {
            document.getElementById("wishlistButton").style.display = data['state'] ? "none" : "block"
            document.getElementById("unwishlistButton").style.display = data['state'] ? "block" : "none"
        });
}
