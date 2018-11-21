/**
 * Created by thgrace on 4/19/16.
 */


    var options = {
        valueNames: ['name', 'type', 'difficulty'],
        page: 15,
        plugins: [
            ListPagination({outerWindow: 8})
        ]
    };

    var userList = new List('search-results', options);
    var updateList = function () {
        var name = new Array();
        var type = new Array();
        var difficulty = new Array();

        $("input:checkbox[name=name]:checked").each(function () {
            name.push($(this).val());
        });

        $("input:checkbox[name=type]:checked").each(function () {
            if($(this).val().indexOf('|') > 0){
               var arr = $(this).val().split('|');
               var arrayLength = arr.length;
               type = type.concat(arr);
               console.log('Multiple values:' + arr);
            }
            else{
               type.push($(this).val());
               console.log('Single values:' + arr);
            }
        });

        $("input:checkbox[name=difficulty]:checked").each(function () {
            difficulty.push($(this).val());
        });

        var values_type = type.length > 0 ? type : null;
        var values_name = name.length > 0 ? name : null;
        var values_difficulty = difficulty.length > 0 ? difficulty : null;

        userList.filter(function (item) {
            var typeTest;
            var nameTest;
            var difficultyTest;

            if(item.values().type.indexOf('|') > 0){
                var typeArr = item.values().type.split('|');
                for(var i = 0; i < typeArr.length; i++){
                    if(_(values_type).contains(typeArr[i])){
                        typeTest = true;
                    }
                }
            }

            return (_(values_type).contains(item.values().type) || !values_type || typeTest)
                        && (_(values_name).contains(item.values().name) || !values_name)
                        && (_(values_difficulty).contains(item.values().difficulty) || !values_difficulty)
        });
    }

    userList.on("updated", function () {
        $('.sort').each(function () {
            if ($(this).hasClass("asc")) {
                $(this).find(".fa").addClass("fa-sort-alpha-asc").removeClass("fa-sort-alpha-desc").show();
            } else if ($(this).hasClass("desc")) {
                $(this).find(".fa").addClass("fa-sort-alpha-desc").removeClass("fa-sort-alpha-asc").show();
            } else {
                $(this).find(".fa").hide();
            }
        });
    });

    var all_type = [];
    var all_name = [];
    var all_difficulty = [];

    updateList();

    _(userList.items).each(function (item) {
        if(item.values().type.indexOf('|') > 0){
            var arr = item.values().type.split('|');
            all_type = all_type.concat(arr);
        }
        else{
            all_type.push(item.values().type)
        }

        all_name.push(item.values().name)
        all_difficulty.push(item.values().difficulty)
    });



// {#    _(all_name).uniq().each(function (item) {#}
// {#        if(item != "") {#}
// {#            $(".nameContainer").append('<br><label><input type="checkbox" name="name" value="' + item + '">' + item + '</label>')#}
// {#        }#}
// {#    });#}

    _(all_type).uniq().each(function (item) {
        if(item != ""){
            // if(item == "text (jsm's hand)"){
            //     $(".typeContainer").append('<br><label><input type="checkbox" name="type" value="' + item + '">' + item + '</label>');
            // }
            //
            // else if(item == "score"){
            //     $(".typeContainer").append('<br><label><input type="checkbox" name="type" value="' + item + '"><i class="material-icons">remove</i></label>');
            // }
            //
            // else if(item == "underlining"){
            //     $(".typeContainer").append('<br><label><input type="checkbox" name="type" value="' + item + '"><i class="material-icons">&#xE165;</i></label>');
            // }
            //
            // else {
                $(".typeContainer").append('<br><label><input type="checkbox" name="type" value="' + item + '"> ' + item + '</label>');
            // }

        }

    });


    $(document).off("change", "input:checkbox[name=type]");
    $(document).on("change", "input:checkbox[name=type]", updateList);
    $(document).off("change", "input:checkbox[name=name]");
    $(document).on("change", "input:checkbox[name=name]", updateList);