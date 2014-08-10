/*!
 * jQuery Collapsible List Plugin v0.2
 * http://github.com/sergiocampama/
 *
 * Based on the Collapsible library by Stephen Morley
 * http://code.stephenmorley.org/javascript/collapsible-lists/
 *
 * Released under the MIT License
 *
 * Date: Mon Oct 15 2012
 */

(function($) {
	$.fn.collapsibleList = function() {
		this.find("li").each(function(i, li) {
			var $this = $(li);
			if($this.children("ul").length > 0) {
				$this.addClass("collapsibleListClosed")
			}
			$this.children("ul")
				.addClass("collapsibleList")
				.children("li")
				.last()
				.addClass("lastChild");
			
			$this.on('mousedown', function(e){
				//Prevents selection of text on subsequent clicks
				e.preventDefault();
			})
			.dblclick(function(e){
				//Prevents clicks from activating parent lis
				e.stopPropagation();
				if($(this).children("ul").length > 0) {
					$(this).toggleClass("collapsibleListClosed collapsibleListOpen");
				}
			});
		});
        
		return this;
	}
})(jQuery);