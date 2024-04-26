var filtersSelected = [];
var filterSearch = "";
var filterSort = "";
var filtertPage = 1;
var filtertAllPages = 1;
var pageSize = parseInt($('#homepage_course_max').val());

Object.defineProperty(Array.prototype, 'flat', {
    value: function(depth = 1) {
      return this.reduce(function (flat, toFlatten) {
        return flat.concat((Array.isArray(toFlatten) && (depth>1)) ? toFlatten.flat(depth-1) : toFlatten);
      }, []);
    }
});

const flatten = (obj) => Object.values(obj).flat();


function filterAddCourse(live_class) {
	console.log(live_class);
    var html = _.template($('#live-class-card-tpl').html())(live_class);
    $("#courses-wrapper .courses-listing").append(html);
}

function filterUpdatePagination(total, current) {
	let pagination = $("#live-class-filter-pages");

	// remove all pages
	pagination.empty();
	for (let page = 1; page <= total; page++) {
	  let $p = $("<span>", {"class": "page", "data-page": page});
	  $p.text(page);
	  if(page == current) $p.addClass("active");
	  $p.click(function(){
		let page = parseInt($(this).data("page"));
		if(page > 0 && page <= filtertAllPages) {
		  filterLoadLiveClasses(filtersSelected, filterSearch, filterSort, page);
		}
	  });
	  pagination.append($p);
	}
}

function filterUpdateSuggestionMsg(isSuggestion, category) {
	if(isSuggestion) {
		$("#suggestion-msg .suggestion-cat").text(category);
		let values = $(".courses-filter #"+category  +"-filter input:checkbox:checked+.form-check-label").map(function () {
		  return $(this).text().replaceAll("\n", "").trim();
		}).get().join(', ');
		if(values != "") {
		  $("#suggestion-msg .suggestion-cat").text(values);
		}
		$("#suggestion-msg").show();
	  } else {
		$("#suggestion-msg").hide();
	  }
}

function filterCoursesUpdated() {
	$("#courses-wrapper .wishlist-icon").click(function(e){
		var course_id = $(this).data('course_id');
		var url = ($(this).hasClass('las')) ? '/api/wishlist/remove/': '/api/wishlist/add/';
		var method = ($(this).hasClass('las')) ? 'DELETE': 'POST';
		var $el = $(this);
		jQuery.ajax({
		  type: method,
		  url: url,
		  data: {'course_key': course_id},
		  success: function (res) {
			$el.toggleClass('las');
			$el.toggleClass('lar');
		  },
		  error: function (xhr) { // if error occured
			alert('Something went wrong!');
		  }
		});
	  });
}


function filterLoadLiveClasses(filters, search, sort, page, should_flatten=true) {
	let allFilters = filters;
  
	  if (should_flatten){
		allFilters = flatten(filters);
	}
	  console.log(allFilters);
  
	  let query_string = new URLSearchParams({
	  filters: allFilters,
	  search: search,
	  sort: sort,
	  page: page
	});
  
  
	  $("#courses-wrapper").addClass('loading');
	  // Load courses and replace them in the courses-wrapper
	  var url = '/api/search/live/courses/';
  
	  jQuery.ajax({
		  type: "GET",
		  url: url,
		  data: {
			  'filters': allFilters.join(),
			  'search': search,
			  'sort': sort,
			  'page': page,
			  page_size: pageSize
		  },
		  success: function (res) {
			  console.log(res);
  
			  // if successfull
			  filtersSelected = filters;
			  filterSearch = search;
			  filterSort = sort;
			  filtertPage = page;
			  filtertAllPages = res.num_pages;
  
			  // remove old courses
			  $("#courses-wrapper .courses-listing").empty();
			  // add new courses
			  let courses = res.results;
			  courses.forEach(course => filterAddCourse(course));
			  // update pagination
			  filterUpdatePagination(res.num_pages, filtertPage);
			  // Update suggestion msg
			  filterUpdateSuggestionMsg(res.is_recommened_courses, res.weightage_category);
  
			  // update filters UI
			  for (var key in filtersSelected) {
				  if (filtersSelected.hasOwnProperty(key)) {
					  let values = filtersSelected[key];
					  if (values.length > 0) {
						  $("#" + key + "-counter").text(values.length);
						  $("#" + key + "-counter").addClass("show");
					  } else {
						  $("#" + key + "-counter").text(0);
						  $("#" + key + "-counter").removeClass("show");
					  }
				  }
			  }
  
			  // collapse all filters
			  $("#filter-accordion .filter-header").addClass("collapsed");
			  $("#filter-accordion .collapse").removeClass("show");
  
			  // update active page
			  $("#live-class-filter-pages .page").removeClass("active");
			  $("#live-class-filter-pages .page[data-page=" + filtertPage + "]").addClass("active");
  
			  // update other stuff
			  filterCoursesUpdated();
  
			  // scroll top
			  $('html, body').animate({
				  scrollTop: $(".courses-container").offset().top
			  }, 500);
		  },
		  error: function (xhr) { // if error occured
			  console.error(xhr.statusText + xhr.responseText);
			  alert("Error occured. please try again");
		  },
		  complete: function () {
			  $("#courses-wrapper").removeClass('loading');
		  },
	  });
  }



function liveClassFilterCollect() {
	let filters = [];
	$(".courses-filter .filter-card").each(function (index) {
		let name = $(this).data("filter");
		let values = $("#" + name + "-filter input:checkbox:checked").map(function () {
			return $(this).val();
		}).get();
		console.log("Filter " + name + ": " + values);
		filters[name] = values;
	});

	// get search
	let search = $("#search-filter input").val() || "";

	// get sort
	let sort = $("#sort-filter select").val() || "";

	filterLoadLiveClasses(filters, search, sort, 1)
}

function isAnySelectedFilter(){
  let filters = [];
	$(".courses-filter .filter-card").each(function (index) {
		let name = $(this).data("filter");
		let values = $("#" + name + "-filter input:checkbox:checked").map(function () {
			return $(this).val();
		}).get();
		filters[name] = values;
	});

	let allFilters = flatten(filters);

	// get search
	let search = $("#search-filter input").val() || "";

	// get sort
	let sort = $("#sort-filter select").val() || "";

	return allFilters.length > 0 || search != "" || sort != ""
}

$(document).ready(function () {

	
	$("#live-class-filter-btn").on("click", function () {
		liveClassFilterCollect();
	});



	$(document).keypress(function(event){
    var keycode = (event.keyCode ? event.keyCode : event.which);
    if(keycode == '13'){
      if (isAnySelectedFilter()){
		$("#live-class-filter-btn").click()
      }
    }
  });

  var input = document.getElementById("filters-auto-complete");
  input.addEventListener("keyup", function(event) {
  if (event.keyCode === 13) {
    $("#live-class-filter-btn").click()
  }
});
	


	$("#live-class-filter-prev").on("click", function () {
		if (filtertPage > 1) {
			filterLoadLiveClasses(filtersSelected, filterSearch, filterSort, filtertPage - 1)
		}
	});


	

	$("#live-class-filter-next").on("click", function () {
		if (filtertPage < filtertAllPages) {
			filterLoadLiveClasses(filtersSelected, filterSearch, filterSort, filtertPage + 1)
		}
	});



	$("#live-class-filter-pages .page").on("click", function () {
		let page = parseInt($(this).data("page"));
		if (page > 0 && page <= filtertAllPages) {
			filterLoadLiveClasses(filtersSelected, filterSearch, filterSort, page)
		}
	});

	$(".filter-input").on("change", function() {
	  
		$("#live-class-filter-btn").click();
	  
});
});
