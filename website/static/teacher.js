// get the table element
var table = document.querySelector('table');

// get the table headers
var ths = table.querySelectorAll('th');

// add click event listeners to the headers
ths.forEach(function(th) {
  th.addEventListener('click', function() {
    // get the column index
    var index = Array.prototype.indexOf.call(ths, th);
    // get the table rows
    var rows = table.querySelectorAll('tbody tr');
    // convert the rows to an array
    var arr = Array.prototype.slice.call(rows);
    // sort the rows based on the column clicked
    arr.sort(function(a, b) {
      var aVal = a.children[index].textContent.trim();
      var bVal = b.children[index].textContent.trim();
      if (aVal < bVal) return -1;
      if (aVal > bVal) return 1;
      return 0;
    });
    // append the sorted rows to the table
    table.querySelector('tbody').innerHTML = '';
    arr.forEach(function(row) {
      table.querySelector('tbody').appendChild(row);
    });
  });
});

//seperate function for pie chart 

var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: ['Points Awarded', 'Points Remaining'],
        datasets: [{
            label: 'Points',
            data: [{{ current_user.points_awarded }}, {{ current_user.remaining_points }}],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});