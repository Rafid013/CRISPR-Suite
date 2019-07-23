$(document).ready(function () {
$('#dtBasicExample').DataTable({
    columnDefs: [{
    orderable: false,
    targets: [2,3,4]
    }]
}
);
$('.dataTables_length').addClass('bs-select');
});