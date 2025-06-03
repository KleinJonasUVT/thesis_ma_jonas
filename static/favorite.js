// JavaScript to toggle course favourites without page reload

function setupFavoriteForms() {
  document.querySelectorAll('.favorite-form').forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const checkbox = form.querySelector('input[type="checkbox"]');
      if (!checkbox) return;
      const courseCode = checkbox.dataset.courseCode;
      const favorited = checkbox.checked;
      const url = favorited ? `/course/${courseCode}/rating` : `/course/${courseCode}/remove_rating`;
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ activity: favorited ? 'favorited' : 'unfavorited' })
      }).then(function(resp) {
        if (resp.ok) {
          form.action = favorited ? `/course/${courseCode}/remove_rating` : `/course/${courseCode}/rating`;
        } else {
          checkbox.checked = !favorited;
        }
      }).catch(function() {
        checkbox.checked = !favorited;
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', setupFavoriteForms);
