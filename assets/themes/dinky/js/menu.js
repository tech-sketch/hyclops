$(document).ready(function(){
    $("ul.responsive_menu").hover(function () {
        console.log("hoge");
        $("ul:not(:animated)", this).slideDown("fast");
        },function(){
            $("ul.menu_list",this).slideUp("fast");
        }
    );
});
